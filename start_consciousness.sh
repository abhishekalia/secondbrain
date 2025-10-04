#!/bin/bash
echo "🧠 Starting Digital Consciousness..."

# Start Ollama in background
ollama serve &
echo "✓ Ollama starting..."
sleep 5

# Start Qdrant
docker start qdrant 2>/dev/null || docker run -d --name qdrant -p 6333:6333 -p 6334:6334 -v ~/secondbrain/qdrant_storage:/qdrant/storage:z qdrant/qdrant:latest
echo "✓ Qdrant starting..."

echo ""
echo "✅ All services running!"
echo ""
echo "Now you can run:"
echo "  python3 capture_patterns.py"
echo "  python3 -m streamlit run consciousness_permanent.py"
