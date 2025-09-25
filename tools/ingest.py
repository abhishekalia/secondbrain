import os, glob, requests
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from pypdf import PdfReader

OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
DATA_DIR = os.path.expanduser("~/ak/data")
COLLECTION = "ak"
QDRANT_URL = "http://localhost:6333"

def read_text_files(folder):
    paths = sorted(glob.glob(os.path.join(folder, "*.txt")) +
                   glob.glob(os.path.join(folder, "*.md")))
    docs = []
    for p in paths:
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.read().strip()
            if txt:
                docs.append({"path": p, "text": txt})
    return docs

def read_pdf_files(folder):
    paths = sorted(glob.glob(os.path.join(folder, "*.pdf")))
    docs = []
    for p in paths:
        try:
            reader = PdfReader(p)
            pages = [page.extract_text() or "" for page in reader.pages]
            txt = "\n".join(pages).strip()
            if txt:
                docs.append({"path": p, "text": txt})
        except Exception as e:
            print(f"[skip pdf] {p}: {e}")
    return docs

def chunk(text, chunk_chars=1800, overlap=200):
    out, i, n = [], 0, len(text)
    while i < n:
        out.append(text[i:i+chunk_chars])
        i += max(1, chunk_chars - overlap)
    return out

def embed_one(text: str):
    js = requests.post(f"{OLLAMA_URL}/api/embeddings",
                       json={"model": EMBED_MODEL, "prompt": text},
                       timeout=120).json()
    if "embedding" in js and isinstance(js["embedding"], list) and js["embedding"]:
        return js["embedding"]
    raise RuntimeError(f"Unexpected embeddings response: {js}")

def main():
    docs = read_text_files(DATA_DIR) + read_pdf_files(DATA_DIR)
    if not docs:
        print("No files found in ~/ak/data (.txt, .md, .pdf). Add some and retry.")
        return

    chunks, metas = [], []
    for d in docs:
        for idx, c in enumerate(chunk(d["text"])):
            chunks.append(c)
            metas.append({"path": d["path"], "chunk_index": idx})

    print(f"Embedding {len(chunks)} chunks with {EMBED_MODEL}…")
    embs = [embed_one(c) for c in chunks]
    dim = len(embs[0])

    q = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
    try:
        q.get_collection(COLLECTION)
        q.delete_collection(COLLECTION)
    except:
        pass
    q.create_collection(
        collection_name=COLLECTION,
        vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE)
    )

    points = [
        rest.PointStruct(id=i, vector=vec, payload={"text": txt, "meta": metas[i]})
        for i, (vec, txt) in enumerate(zip(embs, chunks))
    ]
    q.upsert(collection_name=COLLECTION, points=points)
    print(f"Indexed {len(points)} chunks into '{COLLECTION}' (dim={dim}).")

if __name__ == "__main__":
    main()
