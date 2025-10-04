import streamlit as st
import requests
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Second Brain", 
    page_icon="🧠", 
    layout="wide"
)

# === LOAD ALL DATA ===
def load_mental_states():
    if os.path.exists("my_data/mental_states.json"):
        try:
            with open("my_data/mental_states.json") as f:
                states = json.load(f)
                if states:  # Check if not empty
                    return states
        except:
            pass
    
    # Return default states if file doesn't exist or is empty
    default_states = {
        "🧠": {"name": "pure_logic", "description": "When you're analytical and focused", "patterns": []},
        "🌀": {"name": "spiral", "description": "When you're stuck in loops or overthinking", "patterns": []},
        "⚡": {"name": "flow", "description": "When you're in the zone, creating", "patterns": []},
        "🪞": {"name": "reflection", "description": "When you're introspective", "patterns": []},
        "📘": {"name": "teaching", "description": "When you're explaining things", "patterns": []},
        "😤": {"name": "frustrated", "description": "When things aren't working", "patterns": []},
        "🎯": {"name": "determined", "description": "When you're pushing through", "patterns": []}
    }
    
    # Save default states
    os.makedirs("my_data", exist_ok=True)
    with open("my_data/mental_states.json", "w") as f:
        json.dump(default_states, f, indent=2)
    
    return default_states

def load_patterns():
    patterns = []
    if os.path.exists("my_data/patterns"):
        for file in os.listdir("my_data/patterns"):
            if file.endswith('.json'):
                try:
                    with open(os.path.join("my_data/patterns", file)) as f:
                        patterns.extend(json.load(f))
                except:
                    pass
    return patterns

def load_personality():
    if os.path.exists("my_data/personality_profile.json"):
        try:
            with open("my_data/personality_profile.json") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_journal_entry(entry):
    """Save journal entries persistently"""
    os.makedirs("my_data/journal", exist_ok=True)
    filename = f"my_data/journal/journal_{datetime.now().strftime('%Y%m%d')}.json"
    
    # Load existing entries for today
    entries = []
    if os.path.exists(filename):
        try:
            with open(filename) as f:
                entries = json.load(f)
        except:
            entries = []
    
    # Add new entry
    entries.append(entry)
    
    # Save
    with open(filename, 'w') as f:
        json.dump(entries, f, indent=2)

def load_journal_entries():
    """Load all journal entries"""
    entries = []
    journal_dir = "my_data/journal"
    if os.path.exists(journal_dir):
        for file in sorted(os.listdir(journal_dir)):
            if file.endswith('.json'):
                try:
                    with open(os.path.join(journal_dir, file)) as f:
                        entries.extend(json.load(f))
                except:
                    pass
    return entries

# === INITIALIZE ===
if "mental_states" not in st.session_state:
    st.session_state.mental_states = load_mental_states()
if "patterns" not in st.session_state:
    st.session_state.patterns = load_patterns()
if "personality" not in st.session_state:
    st.session_state.personality = load_personality()
if "journal_messages" not in st.session_state:
    st.session_state.journal_messages = []
if "mirror_messages" not in st.session_state:
    st.session_state.mirror_messages = []
if "all_journal_entries" not in st.session_state:
    st.session_state.all_journal_entries = load_journal_entries()
if "current_state" not in st.session_state:
    st.session_state.current_state = "🧠"  # Default state

# === HEADER ===
st.title("🧠 Second Brain")

# === MENTAL STATE EMOJI BAR ===
if st.session_state.mental_states:
    st.markdown("### 🎭 Mental States Reference")
    
    # Create columns for each state
    emoji_cols = st.columns(len(st.session_state.mental_states))
    
    for idx, (emoji, info) in enumerate(st.session_state.mental_states.items()):
        with emoji_cols[idx]:
            # Make clickable buttons for each state
            if st.button(f"{emoji} {info['name']}", key=f"state_{idx}", use_container_width=True):
                st.session_state.current_state = emoji
                st.rerun()
    
    # Show current state
    st.info(f"**Current State:** {st.session_state.current_state} - {st.session_state.mental_states.get(st.session_state.current_state, {}).get('description', '')}")
else:
    st.warning("Mental states not configured. Creating defaults...")
    st.rerun()

st.divider()

# === MAIN INTERFACE ===
tab1, tab2, tab3 = st.tabs(["📝 Journal (Dump Thoughts)", "🪞 Mirror (See Patterns)", "📊 Analytics"])

# === JOURNAL TAB ===
with tab1:
    st.markdown("*Write freely. No judgment. Just dump your thoughts. Include an emoji to set mental state, or use current state.*")
    
    # Show journal history
    journal_container = st.container(height=400)
    with journal_container:
        for msg in st.session_state.journal_messages:
            with st.chat_message(msg["role"]):
                if msg.get("state"):
                    st.caption(f"State: {msg['state']}")
                st.write(msg["content"])
    
    # Journal input
    journal_input = st.chat_input(f"What's on your mind? (Current: {st.session_state.current_state})")
    
    if journal_input:
        # Detect mental state from message
        detected_state = st.session_state.current_state
        for emoji in st.session_state.mental_states.keys():
            if emoji in journal_input:
                detected_state = emoji
                break
        
        # Add to journal
        journal_entry = {
            "role": "user",
            "content": journal_input,
            "state": detected_state,
            "timestamp": datetime.now().isoformat()
        }
        
        st.session_state.journal_messages.append(journal_entry)
        st.session_state.all_journal_entries.append(journal_entry)
        save_journal_entry(journal_entry)
        
        # Simple acknowledgment (not trying to solve, just listening)
        state_name = st.session_state.mental_states.get(detected_state, {}).get('name', 'unknown')
        response = f"✓ Captured. I see you're in {detected_state} ({state_name}) state."
        
        st.session_state.journal_messages.append({"role": "assistant", "content": response})
        st.rerun()

# === MIRROR TAB ===
with tab2:
    st.markdown("*I'll reflect your patterns back to you. Let's explore together.*")
    
    # Show mirror conversation
    mirror_container = st.container(height=400)
    with mirror_container:
        for msg in st.session_state.mirror_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    
    # Mirror chat input
    mirror_input = st.chat_input(f"Talk to your mirror... (Current state: {st.session_state.current_state})")
    
    if mirror_input:
        # Add user message
        st.session_state.mirror_messages.append({
            "role": "user",
            "content": f"{st.session_state.current_state} {mirror_input}"
        })
        
        # Build context from journal entries
        recent_journal = st.session_state.all_journal_entries[-20:] if st.session_state.all_journal_entries else []
        journal_context = "\n".join([
            f"{e.get('state','')} at {e.get('timestamp','')}: {e.get('content','')}" 
            for e in recent_journal
        ])
        
        # Build system prompt for mirror
        personality = st.session_state.personality
        system_prompt = f"""You are {personality.get('name', 'the user')}'s Second Brain - specifically the Mirror function.

PERSONALITY PROFILE:
Name: {personality.get('name', 'User')}
Traits: {personality.get('description', '')}
Communication style: {personality.get('communication_style', '')}

MENTAL STATES YOU RECOGNIZE:
{json.dumps(st.session_state.mental_states, indent=2)}

LEARNED PATTERNS:
{json.dumps(st.session_state.patterns[-5:], indent=2) if st.session_state.patterns else 'Still learning...'}

RECENT JOURNAL ENTRIES (what's been on their mind):
{journal_context}

YOUR ROLE AS THE MIRROR:
1. Reflect their patterns back clearly
2. Notice connections between journal entries and current state
3. Point out loops they might be in
4. Help them see triggers from their journal entries
5. Mirror their communication style
6. Don't try to fix or advise - just reflect clearly
7. Use their mental state emojis when relevant

Current state: {st.session_state.current_state} - {st.session_state.mental_states.get(st.session_state.current_state, {}).get('description', '')}"""
        
        # Get mirror response
        with st.chat_message("assistant"):
            with st.spinner("Reflecting..."):
                try:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.mirror_messages[-10:]]
                    ]
                    
                    response = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "qwen2.5:7b",
                            "messages": messages,
                            "stream": False,
                            "options": {"temperature": 0.7}
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        content = response.json()["message"]["content"]
                    else:
                        content = "Connection issue. Make sure Ollama is running."
                except Exception as e:
                    content = f"Error: {str(e)}"
                
                st.write(content)
                st.session_state.mirror_messages.append({"role": "assistant", "content": content})
        
        st.rerun()

# === ANALYTICS TAB ===
with tab3:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Journal Entries", len(st.session_state.all_journal_entries))
        st.metric("Patterns Captured", len(st.session_state.patterns))
    
    with col2:
        # Count mental states used
        state_counts = {}
        for entry in st.session_state.all_journal_entries:
            state = entry.get('state', 'unknown')
            state_counts[state] = state_counts.get(state, 0) + 1
        
        st.markdown("**Most Common States:**")
        if state_counts:
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                state_name = st.session_state.mental_states.get(state, {}).get('name', state)
                st.write(f"{state} ({state_name}): {count}x")
        else:
            st.write("No data yet")
    
    with col3:
        st.markdown("**Recent Patterns:**")
        if st.session_state.patterns:
            recent = st.session_state.patterns[-3:]
            for p in recent:
                st.caption(f"{p.get('state', '')} - {p.get('trigger', '')[:30]}...")
        else:
            st.write("No patterns yet")
    
    st.divider()
    
    # Show recent journal entries
    st.markdown("### 📔 Recent Journal Entries")
    if st.session_state.all_journal_entries:
        for entry in reversed(st.session_state.all_journal_entries[-10:]):
            timestamp = entry.get('timestamp', 'Unknown time')[:16] if entry.get('timestamp') else 'Unknown time'
            with st.expander(f"{entry.get('state', '?')} - {timestamp}"):
                st.write(entry.get('content', ''))
    else:
        st.info("No journal entries yet. Start journaling in the Journal tab!")

# === SIDEBAR ===
with st.sidebar:
    st.header("🧠 Second Brain Status")
    
    if st.session_state.personality:
        st.success(f"✅ {st.session_state.personality.get('name', 'User')}")
    else:
        st.warning("⚠️ No personality set")
        if st.button("Set Personality"):
            st.info("Run consciousness_permanent.py to set personality")
    
    st.divider()
    
    st.metric("Total Thoughts", len(st.session_state.all_journal_entries))
    st.metric("Mirror Convos", len(st.session_state.mirror_messages) // 2)  # Divide by 2 for actual conversations
    st.metric("Patterns", len(st.session_state.patterns))
    
    st.divider()
    
    if st.button("💾 Save to GitHub"):
        result = os.system("cd ~/secondbrain && git add . && git commit -m 'Update Second Brain journal and patterns' && git push")
        if result == 0:
            st.success("✅ Saved to GitHub!")
        else:
            st.error("Failed to save. Check git status")
    
    if st.button("📝 Capture New Patterns"):
        st.info("Run in terminal:\npython3 capture_patterns.py")
    
    if st.button("🔄 Refresh Data"):
        st.session_state.mental_states = load_mental_states()
        st.session_state.patterns = load_patterns()
        st.session_state.all_journal_entries = load_journal_entries()
        st.rerun()
    
    st.divider()
    st.caption("Your Second Brain never forgets")
