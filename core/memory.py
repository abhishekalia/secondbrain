import requests

QDRANT_URL = "http://localhost:6333"
COLL_JOURNALS = "journals"
COLL_FACTS = "facts"

def ensure_collections(vector_size: int = 768):
    for coll in (COLL_JOURNALS, COLL_FACTS):
        r = requests.get(f"{QDRANT_URL}/collections/{coll}")
        if r.status_code == 200:
            continue
        create = requests.put(
            f"{QDRANT_URL}/collections/{coll}",
            json={
                "vectors": {"size": vector_size, "distance": "Cosine"},
                "optimizers_config": {"default_segment_number": 1},
            },
            timeout=5,
        )
        create.raise_for_status()

