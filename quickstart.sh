#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo ">> Activating venv"
python3 -m venv .venv || true
source .venv/bin/activate

echo ">> Installing deps"
pip install -U "streamlit>=1.33,<1.39" "requests>=2.31,<3"

echo ">> Starting Ollama (if not running) & pulling model"
ollama serve >/dev/null 2>&1 & sleep 1 || true
ollama pull mistral:latest

echo ">> Starting Qdrant (Docker)"
docker rm -f qdrant 2>/dev/null || true
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest >/dev/null

echo ">> Ensuring collections"
python - <<'PY'
from core.memory import ensure_collections
ensure_collections(768)
print("ok: qdrant collections ready")
PY

echo ">> Launching Streamlit"
python -m streamlit run tools/ak_chat.py --server.port 8513 --server.address 127.0.0.1
