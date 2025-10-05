#!/bin/bash

# Smart Git Push - Only pushes when features are working
# Usage: ./push_to_github.sh "your commit message"

set -e  # Exit on error

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔍 Second Brain Git Push${NC}"
echo "================================"

# Check if we're in the right directory
if [ ! -f "second_brain.py" ]; then
    echo -e "${RED}❌ Error: Not in secondbrain directory${NC}"
    exit 1
fi

# Check for commit message
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Provide a commit message${NC}"
    echo "Usage: ./push_to_github.sh 'your message'"
    exit 1
fi

COMMIT_MSG="$1"

# Check if Ollama is running (feature test)
echo -e "\n${YELLOW}Testing Ollama connection...${NC}"
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${RED}❌ Ollama not running. Start it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Ollama running${NC}"

# Check if qwen2.5:7b is available
echo -e "\n${YELLOW}Checking for qwen2.5:7b model...${NC}"
if ! ollama list | grep -q "qwen2.5:7b"; then
    echo -e "${RED}❌ qwen2.5:7b model not found${NC}"
    echo "Run: ollama pull qwen2.5:7b"
    exit 1
fi
echo -e "${GREEN}✅ Model available${NC}"

# Check Python dependencies
echo -e "\n${YELLOW}Checking Python dependencies...${NC}"
if ! python -c "import streamlit, requests" 2>/dev/null; then
    echo -e "${RED}❌ Missing dependencies${NC}"
    echo "Run: pip install -r requirements.txt"
    exit 1
fi
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Quick syntax check on main files
echo -e "\n${YELLOW}Checking Python syntax...${NC}"
python -m py_compile second_brain.py capture_patterns.py
echo -e "${GREEN}✅ Syntax valid${NC}"

# Git operations
echo -e "\n${YELLOW}Preparing Git commit...${NC}"

# Make sure .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo -e "${YELLOW}⚠️  No .gitignore found, creating one...${NC}"
    cat > .gitignore << 'GITIGNORE_EOF'
# Personal data - NEVER commit this
my_data/
*.json

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Streamlit
.streamlit/

# OS
.DS_Store
GITIGNORE_EOF
fi

# Show what will be committed
echo -e "\n${YELLOW}Files to be committed:${NC}"
git add -n .

# Add files
git add .

# Check if there's anything to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}⚠️  Nothing to commit (no changes)${NC}"
    exit 0
fi

# Show diff summary
echo -e "\n${YELLOW}Changes:${NC}"
git diff --staged --stat

# Commit
echo -e "\n${YELLOW}Committing...${NC}"
git commit -m "$COMMIT_MSG"
echo -e "${GREEN}✅ Committed${NC}"

# Push
echo -e "\n${YELLOW}Pushing to GitHub...${NC}"
if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
    echo -e "${GREEN}✅ Pushed to GitHub successfully!${NC}"
else
    echo -e "${RED}❌ Push failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 All done!${NC}"
echo "Commit: $COMMIT_MSG"
