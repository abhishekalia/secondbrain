import os, glob, requests, sys, re
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
try:
    from pypdf import PdfReader
    PDF_OK = True
except Exception:
    PDF_OK = False

BASE = Path.home() / "ak" / "data"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
QDRANT_URL = "http://localhost:6333"

def to_collection_name(folder: Path) -> str:
    rel = folder.relative_to(BASE)
    parts = ["ak"] + [re.sub(r"[^a-z0-9]+","_", p.lower()) for p in rel.parts]
    return "_".join([p for p in parts if p])

def read_txt_md(folder: Path):
    docs = []
    for p in sorted(list(folder.glob("*.txt")) + list(folder.glob("*.md"))):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore").strip()
            if txt: docs.append({"path": str(p), "text": txt})
        except: pass
    return docs

def read_pdfs(folder: Path):
    docs = []
    if not PDF_OK: return docs
    for p in sorted(folder.glob("*.pdf")):
        try:
            reader = PdfReader(str(p))
            pages = [(page.extract_text() or "") for page in reader.pages]
            txt = "\n".join(pages).strip()
            if txt: docs.append({"path": str(p), "text": txt})
        except Exception as e:
            print(f"[skip pdf] {p}: {e}")
    return docs

def chunk(text, n=1800, overlap=200):
    out=[]; i=0
    while i < len(text):
        out.append(text[i:i+n]); i += max(1, n-overlap)
    return out

def embed_one(t: str):
    js = requests.post(f"{OLLAMA_URL}/api/embeddings",
                       json={"model": EMBED_MODEL, "prompt": t},
                       timeout=120).json()
    if "embedding" in js and js["embedding"]:
        return js["embedding"]
    raise RuntimeError(f"Embedding failed: {js}")

def ingest_folder(folder: Path):
    coll = to_collection_name(folder)
    docs = read_txt_md(folder) + read_pdfs(folder)
    if not docs:
        print(f"[empty] {folder} -> {coll}")
        return None, 0
    chunks, metas = [], []
    for d in docs:
        for idx, c in enumerate(chunk(d["text"])):
            chunks.append(c)
            metas.append({"path": d["path"], "chunk_index": idx})
    print(f"[{coll}] embedding {len(chunks)} chunks from {folder} …")
    embs = [embed_one(c) for c in chunks]
    dim = len(embs[0])
    q = QdrantClient(url=QDRANT_URL, prefer_grpc=False)
    try: q.delete_collection(coll)
    except: pass
    q.create_collection(coll, vectors_config=rest.VectorParams(size=dim, distance=rest.Distance.COSINE))
    points = [rest.PointStruct(id=i, vector=v, payload={"text":t, "meta": metas[i]})
              for i,(v,t) in enumerate(zip(embs, chunks))]
    q.upsert(coll, points=points)
    print(f"[{coll}] indexed {len(points)}")
    return coll, len(points)

def main():
    if not BASE.exists():
        print(f"No data folder at {BASE}"); return
    collections = []
    # Walk only leaf folders that contain files
    for folder, subdirs, files in os.walk(BASE):
        fpath = Path(folder)
        if any(Path(folder).glob("*.txt")) or any(Path(folder).glob("*.md")) or any(Path(folder).glob("*.pdf")):
            coll, n = ingest_folder(fpath)
            if coll: collections.append(coll)
    if not collections:
        print("No ingestable folders found.")
    else:
        print("\nReady collections:")
        for c in sorted(collections):
            print(" -", c)

if __name__ == "__main__":
    main()
