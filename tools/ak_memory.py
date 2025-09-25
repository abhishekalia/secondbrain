import os, sys, json, time, uuid, requests
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

BASE = os.path.expanduser("~/ak")
MEM_FILE = os.path.join(BASE, "memories", "memories.jsonl")
OLLAMA_URL = "http://localhost:11434"
EMB_MODEL = "nomic-embed-text"
QDRANT_URL = "http://localhost:6333"
COLL = "ak_mem"

def ensure_files():
    os.makedirs(os.path.dirname(MEM_FILE), exist_ok=True)
    if not os.path.exists(MEM_FILE):
        open(MEM_FILE, "w").close()

def embed(text: str):
    js = requests.post(f"{OLLAMA_URL}/api/embeddings",
                       json={"model": EMB_MODEL, "prompt": text},
                       timeout=60).json()
    if "embedding" in js and isinstance(js["embedding"], list):
        return js["embedding"]
    raise RuntimeError(f"Unexpected embeddings response: {js}")

def qdrant():
    return QdrantClient(url=QDRANT_URL, prefer_grpc=False)

def ensure_collection(dim: int):
    q = qdrant()
    try:
        q.get_collection(COLL)
        # collection exists; assume dim matches first write. For mismatches, recreate manually.
    except:
        q.create_collection(
            collection_name=COLL,
            vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE)
        )
    return q

def add_memory(text: str, mtype="fact", importance=5):
    ensure_files()
    vec = embed(text)
    q = ensure_collection(len(vec))
    mid = str(uuid.uuid4())  # valid UUID
    rec = {
        "id": mid,
        "type": mtype,
        "text": text,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "importance": importance
    }
    with open(MEM_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    q.upsert(collection_name=COLL, points=[rest.PointStruct(id=mid, vector=vec, payload=rec)])
    print(f"remembered: {mid}")

def recall(query: str, k=5):
    vec = embed(query)
    hits = qdrant().search(collection_name=COLL, query_vector=vec, limit=k)
    for h in hits:
        print(f"{h.payload['id']}: {h.payload['text']}  (score={h.score:.4f})")

def forget(mem_id: str):
    ensure_files()
    rows, found = [], False
    with open(MEM_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except:
                continue
            if obj.get("id") == mem_id and not obj.get("forgotten"):
                obj["forgotten"] = True
                found = True
            rows.append(obj)
    if not found:
        print("not found."); return
    with open(MEM_FILE, "w", encoding="utf-8") as f:
        for obj in rows:
            f.write(json.dumps(obj) + "\n")
    qdrant().delete(collection_name=COLL, points_selector=rest.PointIdsList(points=[mem_id]))
    print(f"forgot: {mem_id}")

def usage():
    print("Usage:")
    print("  python tools/ak_memory.py remember \"text\" [type] [importance]")
    print("  python tools/ak_memory.py recall \"query\" [k]")
    print("  python tools/ak_memory.py forget <mem_id>")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        usage(); sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "remember":
        text = sys.argv[2]
        mtype = sys.argv[3] if len(sys.argv) > 3 else "fact"
        importance = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        add_memory(text, mtype, importance)
    elif cmd == "recall":
        query = sys.argv[2]
        k = int(sys.argv[3]) if len(sys.argv) > 3 else 5
        recall(query, k)
    elif cmd == "forget":
        mem_id = sys.argv[2]
        forget(mem_id)
    else:
        usage()
