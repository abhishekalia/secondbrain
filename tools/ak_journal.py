#!/usr/bin/env python3
import os, sys, time, json, requests, uuid, subprocess, shlex
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

BASE = Path.home() / "ak"
DATA_JOURNAL = BASE / "data" / "journal"
MEM_FILE = BASE / "memories" / "memories.jsonl"
OLLAMA = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "mistral"
QDRANT_URL = "http://localhost:6333"
MEM_COLL = "ak_mem"

def ensure_dirs():
    DATA_JOURNAL.mkdir(parents=True, exist_ok=True)
    MEM_FILE.parent.mkdir(parents=True, exist_ok=True)

def append_entry(text: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"### {ts}\n{text}\n\n"
    p = DATA_JOURNAL / "entries.md"
    with open(p, "a", encoding="utf-8") as f:
        f.write(entry)
    return str(p), ts

def embed_one(text: str):
    r = requests.post(f"{OLLAMA}/api/embeddings", json={"model": EMBED_MODEL, "prompt": text}, timeout=60)
    js = r.json()
    if "embedding" in js:
        return js["embedding"]
    if "data" in js and js["data"] and "embedding" in js["data"][0]:
        return js["data"][0]["embedding"]
    raise RuntimeError(f"Unexpected embedding response: {js}")

def qdrant_client():
    return QdrantClient(url=QDRANT_URL, prefer_grpc=False)

def ensure_collection(dim:int):
    q = qdrant_client()
    try:
        q.get_collection(MEM_COLL)
    except:
        q.create_collection(collection_name=MEM_COLL, vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE))
    return q

def upsert_memory(text:str, mtype="journal", importance=5):
    vec = embed_one(text)
    q = ensure_collection(len(vec))
    mid = str(uuid.uuid4())
    rec = {"id": mid, "type": mtype, "text": text, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "importance": importance}
    with open(MEM_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    q.upsert(collection_name=MEM_COLL, points=[rest.PointStruct(id=mid, vector=vec, payload=rec)])
    return mid


def extract_facts_from_entry(entry_text: str):
    # Ask Mistral to extract up to 3 concise facts as JSON
    prompt = "Extract up to three concise facts from the following journal entry. Output a JSON array of objects with keys: type (habit|preference|mood|task|insight), text."
    messages = [
        {"role":"system","content":"You are a concise extractor. Output only JSON."},
        {"role":"user","content": prompt + "\n\n" + entry_text}
    ]
    # Force non-streaming so we get one JSON response
    r = requests.post(f"{OLLAMA}/api/chat",
                      json={"model": CHAT_MODEL, "messages": messages, "stream": False},
                      timeout=60)
    # Try strict JSON first
    try:
        js = r.json()
    except Exception:
        # Fall back to raw text if server returned concatenated JSON
        raw = r.text
        # Try to find a JSON array in the text
        import re, json as _json
        m = re.search(r'(\[.*\])', raw, flags=re.S)
        return _json.loads(m.group(1)) if m else []
    # Normal shapes
    content = ""
    if isinstance(js, dict):
        if "message" in js and isinstance(js["message"], dict) and "content" in js["message"]:
            content = js["message"]["content"]
        elif "messages" in js and js["messages"]:
            content = js["messages"][-1].get("content","")
    # Extract JSON array from content
    import re, json as _json
    m = re.search(r'(\[.*\])', content, flags=re.S)
    if not m:
        return []
    try:
        return _json.loads(m.group(1))
    except Exception:
        return []


def main():
    ensure_dirs()
    if len(sys.argv) == 1 or sys.argv[1] == "--edit":
        editor = os.environ.get("EDITOR", "vi")
        tmp = BASE / "tmp_journal.txt"
        if tmp.exists(): tmp.unlink()
        subprocess.call([editor, str(tmp)])
        if not tmp.exists(): 
            print("No entry written."); return
        text = tmp.read_text(encoding="utf-8").strip()
        tmp.unlink()
    else:
        text = " ".join(sys.argv[1:]).strip()
    if not text:
        print("Empty entry. Abort."); return
    path, ts = append_entry(text)
    mid = upsert_memory(text, mtype="journal", importance=7)
    facts = extract_facts_from_entry(text)
    extracted_ids = []
    for f in facts:
        ftext = f.get("text")
        ftype = f.get("type","insight")
        if ftext:
            fid = upsert_memory(ftext, mtype=ftype, importance=6)
            extracted_ids.append((fid, ftype, ftext))
    print(f"Journal saved to {path} at {ts}")
    print(f"Journal memory id: {mid}")
    if extracted_ids:
        print("Extracted facts stored:")
        for fid,ftype,ftext in extracted_ids:
            print(f" - {fid} [{ftype}] {ftext}")

if __name__ == '__main__':
    main()
