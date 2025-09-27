# secondbrain (AK’s Local Jarvis)

Witty, precise, no fluff. Local Streamlit chat UI + Ollama (Mistral) + Qdrant memory.

## Architecture
- **UI:** Streamlit (`tools/ak_chat.py`)
- **LLM:** Ollama → `mistral:latest` at `http://localhost:11434/api/chat`
- **Memory:** Qdrant (Docker) at `http://localhost:6333`
- **Core:** `core/llm.py`, `core/prompt.py`, `core/memory.py`
- **Data:** `memories/memories.jsonl` (append-only journals/facts)

## Prereqs
- macOS
- Python 3.9+
- Docker Desktop (running)
- Ollama (installed)

## Setup (first time)
```bash
cd ~/ak
python3 -m venv .venv && source .venv/bin/activate
pip install -U "streamlit>=1.33,<1.39" "requests>=2.31,<3"

# LLM
ollama serve >/dev/null 2>&1 &  # background
ollama pull mistral:latest

# Qdrant
docker rm -f qdrant 2>/dev/null || true
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest

