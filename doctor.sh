#!/usr/bin/env bash
set -euo pipefail

echo "== Python/venv =="
python -V || true
which python || true

echo "== Ports (8513,11434,6333) =="
for p in 8513 11434 6333; do
  echo -n "Port $p: "
  lsof -i :$p -sTCP:LISTEN || echo "free"
done

echo "== Ollama tags =="
curl -s http://localhost:11434/api/tags || echo "ollama not responding"

echo "== LLM chat =="
curl -s -X POST http://localhost:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"mistral:latest","messages":[{"role":"user","content":"hi"}],"stream":false}' \
  | python -c 'import sys,json; j=json.load(sys.stdin); print(j.get("message",{}).get("content"))' || true

echo "== Qdrant status =="
curl -s http://localhost:6333/collections || echo "qdrant not responding"

echo "== Memories head =="
[ -f memories/memories.jsonl ] && head -n 3 memories/memories.jsonl || echo "no memories.jsonl"

echo "== Streamlit syntax =="
python -m py_compile tools/ak_chat.py || true

echo "OK"
