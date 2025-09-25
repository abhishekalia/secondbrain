import os, json, glob, requests, streamlit as st, subprocess, shlex
from pathlib import Path
from qdrant_client import QdrantClient

BASE = os.path.expanduser("~/ak")
OLLAMA_URL = "http://localhost:11434"
GEN_MODEL  = "mistral"
EMB_MODEL  = "nomic-embed-text"
QDRANT_URL = "http://localhost:6333"
MEM_COLL   = "ak_mem"
MEMLOG     = os.path.expanduser("~/ak/memories/memories.jsonl")

# ---------- helpers
def read_persona():
    p = Path(BASE) / "personality.txt"
    return p.read_text(encoding="utf-8").strip() if p.exists() else "You are AK — concise, sharp, no fluff. If unsure, say so."

def embed_one(text: str):
    js = requests.post(f"{OLLAMA_URL}/api/embeddings",
                       json={"model": EMB_MODEL, "prompt": text},
                       timeout=60).json()
    return js.get("embedding")

def qclient(): 
    return QdrantClient(url=QDRANT_URL, prefer_grpc=False)

def search_collection(coll, qvec, k=3):
    try: 
        return qclient().search(collection_name=coll, query_vector=qvec, limit=k)
    except: 
        return []

def chat(messages):
    js = requests.post(f"{OLLAMA_URL}/api/chat",
                       json={"model": GEN_MODEL, "messages": messages, "stream": False, "options": {"num_ctx": 8192}},
                       timeout=120).json()
    if "message" in js and "content" in js["message"]: 
        return js["message"]["content"]
    if isinstance(js, dict) and "messages" in js: 
        return js["messages"][-1]["content"]
    return "Unexpected chat response."

def memory_cmd(cmd: str):
    mem_py = os.path.join(BASE, "tools", "ak_memory.py")
    if cmd.lower().startswith("remember:"):
        body = cmd.split(":",1)[1].strip()
        parts = [p.strip() for p in body.split("|")]
        text = parts[0] if parts else ""
        mtype = parts[1] if len(parts)>=2 and parts[1] else "fact"
        importance = parts[2] if len(parts)>=3 and parts[2] else "5"
        if not text: return "Usage: remember: <text> [| <type> | <importance>]"
        return subprocess.getoutput(f"python {shlex.quote(mem_py)} remember {shlex.quote(text)} {shlex.quote(mtype)} {shlex.quote(importance)}")
    if cmd.lower().startswith("recall:"):
        q = cmd.split(":",1)[1].strip()
        if not q: return "Usage: recall: <query>"
        return subprocess.getoutput(f"python {shlex.quote(mem_py)} recall {shlex.quote(q)} 5")
    if cmd.lower().startswith("forget:"):
        mid = cmd.split(":",1)[1].strip()
        if not mid: return "Usage: forget: <memory_id>"
        return subprocess.getoutput(f"python {shlex.quote(mem_py)} forget {shlex.quote(mid)}")
    return None

def log_answer(q, a, sources, good):
    log_py = os.path.join(BASE, "tools", "ak_log.py")
    q_ = shlex.quote(q); a_ = shlex.quote(a[:2000]); s_ = shlex.quote(sources or "")
    subprocess.getoutput(f"python {log_py} {q_} {a_} {s_} {good}")

def read_latest_insights():
    base = Path(BASE) / "logs"
    files = sorted(glob.glob(str(base / "insights-*.md")))
    if not files: return None
    try: return Path(files[-1]).read_text(encoding="utf-8")[:4000]
    except: return None

def read_recent_journals(n=7):
    rows=[]
    try:
        with open(MEMLOG,'r',encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if rec.get('type')=='journal':
                        rows.append((rec.get('timestamp',''), (rec.get('text') or '').strip()))
                except: 
                    pass
    except FileNotFoundError:
        return []
    rows.sort(key=lambda x: x[0])   # by timestamp
    return rows[-n:]

def journals_on(date_key):
    out=[]
    try:
        with open(MEMLOG,'r',encoding='utf-8') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    if rec.get('type')=='journal' and rec.get('timestamp','').startswith(date_key):
                        out.append((rec.get('timestamp',''), (rec.get('text') or '').strip()))
                except: pass
    except FileNotFoundError:
        return []
    out.sort(key=lambda x: x[0])
    return out

# ---------- UI
st.set_page_config(page_title="AK — Project Second Brain", layout="wide")
st.title("AK — Project Second Brain")

# Sidebar
with st.sidebar:
    st.checkbox("Grounded-only answers", value= False, key="strict_grounded")
    st.caption("ON = cite files only; OFF = normal chat")

    st.subheader("Status")
    st.caption("• Ollama :11434  • Qdrant :6333  • ctx=8192")
    st.subheader("Recent journals")
    jrns = read_recent_journals(7)
    if jrns:
        for ts, sn in jrns[::-1]:
            sn_clean = sn[:140].replace("\n", " ")
            st.markdown(f"- **{ts}** — {sn_clean}")
    else:
        st.caption("No journals yet. Use: `python tools/ak_journal.py --edit`")
    st.subheader("Insights (last 7 days)")
    latest = read_latest_insights()
    if latest: st.markdown(latest)
    else: st.caption("Run: `python tools/ak_insights.py`")

if "history" not in st.session_state: 
    st.session_state.history = []  # list of dicts {q,a,sources}

persona = read_persona()
user_input = st.text_input("Ask AK", placeholder="")
ask = st.button("Send")

if ask and user_input.strip():
    ql = user_input.strip().lower()

    # deterministic journal handlers (no LLM)
    if ql.startswith("journal on:"):
        # supports YYYY-MM-DD or "Sep 21"
        date_str = user_input.split(":",1)[1].strip()
        from datetime import datetime
        date_key = None
        for fmt in ("%Y-%m-%d","%b %d","%B %d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                year = dt.year if "%Y" in fmt else datetime.now().year
                date_key = f"{year:04d}-{dt.month:02d}-{dt.day:02d}"
                break
            except: pass
        if not date_key:
            ans = "Use: `journal on: YYYY-MM-DD` or `journal on: Sep 21`"
        else:
            rows = journals_on(date_key)
            if not rows:
                ans = f"No journal entries on {date_key}."
            else:
                lines = [f"- {ts} — {txt}" for ts,txt in rows]
                ans = "Journals on " + date_key + ":\n" + "\n".join(lines)
        st.session_state.history.append({"q": user_input, "a": ans, "sources": ""})

    elif ("last journal" in ql) or ("last entry" in ql) or ("what did i journal" in ql):
        rows = read_recent_journals(1)
        if not rows:
            ans = "No journal entries found."
        else:
            ts, txt = rows[-1]
            ans = f"Last journal ({ts}):\n{txt}"
        st.session_state.history.append({"q": user_input, "a": ans, "sources": ""})

    else:
        # memory commands
        out = memory_cmd(user_input.strip())
        if out is not None:
            st.session_state.history.append({"q": user_input, "a": out, "sources": ""})
        else:
            # RAG answer
            qvec = embed_one(user_input.strip())
            if not qvec:
                st.session_state.history.append({"q": user_input, "a": "Embedding failed. Is Ollama running?", "sources": ""})
            else:
                doc_hits = []
                for name in ['ak_identity','ak_artistry','ak_engineering','ak_philosophy','ak_entrepreneurship','ak_client_matterhorn','ak_notes']:
                    try: 
                        doc_hits += search_collection(name, qvec, k=3)
                    except: 
                        pass
                mem_hits = search_collection(MEM_COLL, qvec, k=3)

                ctx_blocks, sources = [], []
                for h in doc_hits:
                    ctx_blocks.append((h.score, (h.payload.get("text") or "").strip()))
                    m = h.payload.get("meta", {})
                    sources.append(os.path.basename(m.get("path","?")) + f"#chunk{m.get('chunk_index','?')}")
                for h in mem_hits:
                    ctx_blocks.append((h.score, (h.payload.get("text") or "").strip()))
                    pid = h.payload.get("id","?"); t = h.payload.get("type","fact")
                    sources.append(f"mem:{t}:{pid[:8]}")
                ctx_blocks = [c for _, c in sorted(ctx_blocks, key=lambda x: x[0], reverse=True)[:5]]
                context_text = "\n\n---\n".join(ctx_blocks) if ctx_blocks else "NO_CONTEXT"

                system_prompt = f"""{persona}
Rules:
- Use context (docs + memories) if helpful; otherwise say context wasn't helpful.
- Be concise and practical. Cite specific items like [sources: file.md, mem:preference:abcd1234].
"""
                user_prompt = f"Question: {user_input}\n\nContext:\n{context_text}\n"
                msgs = [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}]
                ans = chat(msgs).strip()
                if sources:
                    ans += "\n\n[sources: " + ", ".join(dict.fromkeys(sources)) + "]"
                log_answer(user_input, ans, ", ".join(dict.fromkeys(sources)), "neutral")
                st.session_state.history.append({"q": user_input, "a": ans, "sources": ", ".join(dict.fromkeys(sources))})

# History with feedback
for item in st.session_state.history[-50:]:
    st.markdown(f"**You:** {item['q']}")
    st.markdown(f"**AK:** {item['a']}")
    col1, col2 = st.columns(2)
    if col1.button("👍 Good", key=item['q']+"g"):
        log_answer(item['q'], item['a'], item['sources'], "good"); st.success("Logged 👍")
    if col2.button("👎 Bad", key=item['q']+"b"):
        log_answer(item['q'], item['a'], item['sources'], "bad"); st.warning("Logged 👎")
    st.markdown("---")
