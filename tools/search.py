import sys, requests
from qdrant_client import QdrantClient

OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
QDRANT_URL = "http://localhost:6333"
COLLECTION = "ak"

def embed_one(text: str):
    js = requests.post(f"{OLLAMA_URL}/api/embeddings",
                       json={"model": EMBED_MODEL, "prompt": text},
                       timeout=60).json()
    if "embedding" in js and isinstance(js["embedding"], list):
        return js["embedding"]
    raise RuntimeError(f"Unexpected embeddings response: {js}")

query = " ".join(sys.argv[1:]) or "notes"
emb = embed_one(query)

q = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
hits = q.search(collection_name=COLLECTION, query_vector=emb, limit=3)
for i, h in enumerate(hits, 1):
    txt = h.payload["text"].strip().replace("\n"," ")[:160]
    print(f"{i}. score={h.score:.4f}  {txt}")
