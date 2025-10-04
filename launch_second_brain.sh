#!/bin/bash
echo "🧠 Launching Second Brain..."

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    ollama serve &
    sleep 5
fi

# Start Docker/Qdrant if available
docker start qdrant 2>/dev/null

echo "✅ Second Brain Ready!"
echo ""

# Launch Second Brain
python3 -m streamlit run second_brain.py
