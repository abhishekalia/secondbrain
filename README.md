# Second Brain

**Your digital consciousness. Brutally honest. Remembers everything.**

A local AI system that detects your mental state, remembers all conversations, and thinks with you — not for you.

---

## What It Does

- **Auto-detects mental states** (🧠 logic, 🌀 spiral, ⚡ flow, 🪞 reflection, 📘 teaching, 😤 frustrated, 🎯 determined)
- **Remembers everything** - all conversations, patterns, context
- **Brutally honest feedback** - calls out loops, contradictions, BS
- **Context-aware responses** - uses your history to think better
- **Fully local & private** - your data never leaves your machine

---

## Architecture
second_brain.py          # Main Streamlit interface
capture_patterns.py      # Manual pattern capture tool
my_data/
├── journal/                      # Journal entries
├── patterns/                     # Captured thinking patterns
├── conversations.json            # Master conversation log (last 10k)
├── conversations_YYYYMMDD.json   # Daily snapshots
├── state_learning.json           # Learned patterns per state
└── personality_profile.json      # Your profile

**Tech Stack:**
- **UI**: Streamlit
- **LLM**: Ollama → Qwen 2.5 7B (`qwen2.5:7b`)
- **Memory**: JSON files (local, append-only)
- **State Detection**: Pattern matching + confidence scoring

---

## Setup

### Prerequisites
- macOS (or Linux)
- Python 3.9+
- [Ollama](https://ollama.ai) installed

### Install
```bash
# Clone repo
cd ~
git clone https://github.com/abhishekalia/secondbrain.git
cd secondbrain

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install streamlit requests

# Pull LLM model
ollama pull qwen2.5:7b

# Create data directory
mkdir -p my_data/journal my_data/patterns
Run
bash# Start Ollama (if not running)
ollama serve

# In another terminal:
source .venv/bin/activate
streamlit run second_brain.py
Open browser to http://localhost:8501

How to Use
1. Just Talk
Type anything. The system auto-detects your mental state and responds accordingly.
2. Capture Patterns (Optional)
bashpython capture_patterns.py
Manually log your thinking patterns, triggers, responses.
3. Review Memory
Check sidebar for:

Total memories
Today's activity
State distribution
Pattern insights


Mental States
StateEmojiWhen It TriggersLogic🧠Analytical thinking, reasoning, evidence-basedSpiral🌀Overthinking, loops, "can't stop thinking about X"Flow⚡In the zone, crushing it, everything clickingReflection🪞Noticing patterns, meta-awareness, "hmm interesting"Teaching📘Explaining concepts, "so basically..."Frustrated😤Things not working, angry, "why isn't this..."Determined🎯Focused, decisive, "let's get this done"

How State Detection Works

Pattern Matching: Checks text for state-specific keywords
Structure Analysis: Looks at sentence structure, punctuation
Confidence Scoring: 0-95% based on matches
Learning: Stores patterns in state_learning.json to improve over time


Memory System
Every interaction is saved:

Daily files: conversations_YYYYMMDD.json
Master log: Last 10,000 messages in conversations.json
Context building: Searches related memories by keywords
Pattern tracking: Identifies recurring triggers and responses


System Prompt Philosophy
Second Brain is not a friendly assistant. It's the voice in your head that:

Calls out bullshit
Exposes contradictions
Challenges assumptions
Shows you patterns you're blind to
Never sugarcoats

Maximum truth, minimum fluff.

Roadmap
Next Features

 Auto-pattern extraction (no manual capture needed)
 Mental state timeline visualization
 Weekly/monthly pattern reports
 Smarter state detection (learns from corrections)
 Proactive pattern alerts
 Better semantic search

Future

 Fine-tune Qwen on personal conversation patterns
 Predictive state detection
 Multi-modal input (voice, images)


Privacy
Everything runs locally.

No cloud APIs
No data leaves your machine
All memory stored in my_data/ (git-ignored)


Contributing
This is a personal system, but ideas/PRs welcome.
Before pushing:

Test features work
Update this README if architecture changes
Don't commit my_data/ (it's in .gitignore)


License
MIT - Do whatever you want with it.

Questions?
Open an issue or just talk to your Second Brain about it. It remembers everything anyway.
