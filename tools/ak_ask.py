import os, sys, requests, subprocess, shlex
from qdrant_client import QdrantClient

BASE       = os.path.expanduser("~/ak")
OLLAMA_URL = "http://localhost:11434"
GEN_MODEL  = "mistral"
EMB_MODEL  = "nomic-embed-text"
QDRANT_URL = "http://localhost:6333"
DOCS_COLL  = "ak_notes"
MEM_COLL   = "ak_mem"
MEMLOG     = os.path.expanduser("~/ak/memories/memories.jsonl")

def read_persona():
    p1 = os.path.join(BASE, "personalty.txt")   # backwards-compat typo
    p2 = os.path.join(BASE, "personality.txt")
    path = p1 if os.path.exists(p1) else p2
    try:
        return open(path, "r", encoding="utf-8").read().strip()
    except:
        return "You are AK — concise, sharp, no fluff. If unsure, say so."

def embed_one(text: str):
    js = requests.post(f"{OLLAMA_URL}/api/embeddings",
                       json={"model": EMB_MODEL, "prompt": text},
                       timeout=60).json()
    if "embedding" in js:
        return js["embedding"]
    raise RuntimeError(f"Unexpected embeddings response: {js}")

def search_collection(coll: str, query_vec, k=3):
    q = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
    try:
        return q.search(collection_name=coll, query_vector=query_vec, limit=k)
    except Exception:
        return []

def chat(messages):
    js = requests.post(f"{OLLAMA_URL}/api/chat",
                       json={"model": GEN_MODEL, "messages": messages, "stream": False, "options": {"num_ctx": 8192}},
                       timeout=120).json()
    if "message" in js and "content" in js["message"]:
        return js["message"]["content"]
    if isinstance(js, dict) and "messages" in js:
        return js["messages"][-1]["content"]
    raise RuntimeError(f"Unexpected chat response: {js}")

def fmt_source(hit, source_type):
    meta = hit.payload.get("meta", {})
    if source_type == "doc":
        path = meta.get("path", "?")
        idx = meta.get("chunk_index", "?")
        return os.path.basename(path) + f"#chunk{idx}"
    else:
        pid = hit.payload.get("id", "?")
        t = hit.payload.get("type", "fact")
        return f"mem:{t}:{pid[:8]}"

def handle_command(raw: str):
    import subprocess, shlex, os
    BASE = os.path.expanduser('~/ak')
    mem_py = os.path.join(BASE, 'tools', 'ak_memory.py')
    shell_py = os.path.join(BASE, 'tools', 'ak_shell.py')
    journal_py = os.path.join(BASE, 'tools', 'ak_journal.py')

    import os
    mem_py = os.path.join(BASE, "tools", "ak_memory.py")
    shell_py = os.path.join(BASE, "tools", "ak_shell.py")
    cmd = raw.strip()

    if cmd.lower().startswith("remember:"):
        body = cmd.split(":", 1)[1].strip()
        parts = [p.strip() for p in body.split("|")]
        text = parts[0] if parts else ""
        mtype = parts[1] if len(parts) >= 2 and parts[1] else "fact"
        importance = parts[2] if len(parts) >= 3 and parts[2] else "5"
        if not text:
            print("Usage: remember: <text> [| <type> | <importance>]")
            return True
        args = f'python {shlex.quote(mem_py)} remember {shlex.quote(text)} {shlex.quote(mtype)} {shlex.quote(importance)}'
        print(subprocess.getoutput(args))
        return True

    if cmd.lower().startswith("recall:"):
        q = cmd.split(":", 1)[1].strip()
        if not q:
            print("Usage: recall: <query>")
            return True
        args = f'python {shlex.quote(mem_py)} recall {shlex.quote(q)} 5'
        print(subprocess.getoutput(args))
        return True

    if cmd.lower().startswith("forget:"):
        mid = cmd.split(":", 1)[1].strip()
        if not mid:
            print("Usage: forget: <memory_id>")
            return True
        args = f'python {shlex.quote(mem_py)} forget {shlex.quote(mid)}'
        print(subprocess.getoutput(args))
        return True

    if cmd.lower().startswith("run:"):
        body = cmd.split(":", 1)[1].strip()
        if not body:
            print("Usage: run: <command>")
            return True
        args = f'python {shlex.quote(shell_py)} {shlex.quote(body)}'
        print(subprocess.getoutput(args))
        return True

    if raw.lower().startswith('journal:'):
        body = raw.split(':', 1)[1].strip()
        if not body:
            print('Usage: journal: <entry>'); return True
        args = f"python {shlex.quote(journal_py)} {shlex.quote(body)}"
        print(subprocess.getoutput(args)); return True

    return False

def _load_journals():
    out=[]
    try:
        import json
        with open(MEMLOG,'r',encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if rec.get('type')=='journal':
                        out.append((rec.get('timestamp',''), (rec.get('text') or '').strip()))
                except: pass
    except FileNotFoundError:
        pass
    out.sort(key=lambda x: x[0])
    return out

# --- Entry
question = " ".join(sys.argv[1:]).strip()
if not question:
    print("Usage:")
    print("  python tools/ak_ask.py <your question>")
    print("  python tools/ak_ask.py 'remember: text | type | importance'")
    print("  python tools/ak_ask.py 'recall: query'")
    print("  python tools/ak_ask.py 'forget: <mem_id>'")
    print("  python tools/ak_ask.py 'run: <command>'")
    sys.exit(0)

# Intercept memory/shell commands
if handle_command(question):
    sys.exit(0)

# Normal QA
persona = read_persona()
# NL_JOURNAL_INTENT
ql = question.lower().strip()
if ('last journal' in ql) or ('last entry' in ql) or ('what did i journal' in ql) or ('what was my last journal' in ql):
    rows = _load_journals()
    if not rows:
        print('No journal entries found.'); sys.exit(0)
    ts, txt = rows[-1]
    print(f"Last journal ({ts}):\n{txt}"); sys.exit(0)


use = "all"
if question.lower().startswith("use:"):
    head, rest = question.split(":",1)
    use = rest.strip().split()[0].lower()
    question = question.split(None, 1)[1] if " " in question else ""
    if not question:
        print("Example: use: notes What do my notes say?"); exit(0)

qvec = embed_one(question)

doc_hits = []
mem_hits = search_collection(MEM_COLL,  qvec, k=3)
doc_hits = []
for name in ['ak_identity','ak_artistry','ak_engineering','ak_philosophy','ak_entrepreneurship','ak_client_matterhorn','ak_notes']:
    if use in ('all', name.replace('ak_','')):
        doc_hits += search_collection(name, qvec, k=3)

ctx_pairs, sources = [], []
for h in doc_hits:
    ctx_pairs.append((h.score, (h.payload.get("text") or "").strip()))
    sources.append(fmt_source(h, "doc"))
for h in mem_hits:
    ctx_pairs.append((h.score, (h.payload.get("text") or "").strip()))
    sources.append(fmt_source(h, "mem"))

ctx_pairs = [c for _, c in sorted(ctx_pairs, key=lambda x: x[0], reverse=True)[:5]]
context_text = "\n\n---\n".join(ctx_pairs) if ctx_pairs else "NO_CONTEXT"

system_prompt = f"""{persona}
Rules:
- Use context (docs + memories) if helpful; otherwise state that context wasn't helpful.
- Be concise and practical. If you reference specific items from context, cite them like [sources: file.md, mem:preference:abcd1234].
"""

user_prompt = f"""Question: {question}

Context:
{context_text}
"""

msgs = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
]

answer = chat(msgs)

# Build unique sources list BEFORE logging
uniq = []
for s in sources:
    if s not in uniq:
        uniq.append(s)

# Log (neutral by default)
log_py = os.path.expanduser('~/ak/tools/ak_log.py')
sources_str = ', '.join(uniq) if uniq else ''
q_esc = shlex.quote(question)
a_esc = shlex.quote(answer[:2000])
s_esc = shlex.quote(sources_str)
subprocess.getoutput(f"python {log_py} {q_esc} {a_esc} {s_esc} neutral")

# Output
print("\n" + answer.strip())
if uniq:
    print(f"\n[sources: {', '.join(uniq)}]")
