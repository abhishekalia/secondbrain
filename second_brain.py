import streamlit as st
import requests
import json
import os
import subprocess
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
                if states:
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
    
    entries = []
    if os.path.exists(filename):
        try:
            with open(filename) as f:
                entries = json.load(f)
        except:
            entries = []
    
    entries.append(entry)
    
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

def detect_all_states_in_text(text, mental_states):
    """Detect all mental state emojis in text and their positions"""
    states_found = []
    for emoji in mental_states.keys():
        if emoji in text:
            # Find all positions of this emoji
            idx = 0
            while idx < len(text):
                idx = text.find(emoji, idx)
                if idx == -1:
                    break
                states_found.append((idx, emoji))
                idx += 1
    # Sort by position in text
    states_found.sort(key=lambda x: x[0])
    return states_found

def save_to_github():
    """Save all changes to GitHub"""
    try:
        # Change to project directory
        os.chdir(os.path.expanduser("~/secondbrain"))
        
        # Git commands
        commands = [
            "git add .",
            "git commit -m 'Update Second Brain: journal entries and patterns'",
            "git push origin main"
        ]
        
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                # Try with master branch if main fails
                if "git push" in cmd and "main" in cmd:
                    result = subprocess.run("git push origin master", shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        return True, "Saved to GitHub (master branch)"
                
                # Check if it's just "nothing to commit"
                if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                    return True, "Already up to date"
                    
                return False, f"Error: {result.stderr}"
        
        return True, "Successfully saved to GitHub!"
    except Exception as e:
        return False, f"Error: {str(e)}"

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
    st.session_state.current_state = "🧠"

# === HEADER ===
st.title("🧠 Second Brain")

# === MENTAL STATE EMOJI BAR ===
if st.session_state.mental_states:
    st.markdown("### 🎭 Mental States Reference")
    
    # Create two rows for better visibility
    st.markdown("**Click to set current state, or type any emoji in your journal to track state changes:**")
    
    emoji_cols = st.columns(len(st.session_state.mental_states))
    
    for idx, (emoji, info) in enumerate(st.session_state.mental_states.items()):
        with emoji_cols[idx]:
            # Highlight current state
            is_current = emoji == st.session_state.current_state
            button_type = "primary" if is_current else "secondary"
            
            if st.button(
                f"{emoji} {info['name']}", 
                key=f"state_{idx}", 
                use_container_width=True,
                type=button_type
            ):
                st.session_state.current_state = emoji
                st.rerun()
            
            # Show description on hover (as caption)
            st.caption(info['description'][:40] + "...")
    
    # Show current state prominently
    current_desc = st.session_state.mental_states.get(st.session_state.current_state, {}).get('description', '')
    st.success(f"**Current State:** {st.session_state.current_state} - {current_desc}")

st.divider()

# === MAIN INTERFACE ===
tab1, tab2, tab3 = st.tabs(["📝 Journal (Dump Thoughts)", "🪞 Mirror (See Patterns)", "📊 Analytics"])

# === JOURNAL TAB ===
with tab1:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("*Write freely. Add emojis anywhere to track state changes during journaling.*")
    with col2:
        st.info(f"Default state: {st.session_state.current_state}")
    
    # Show journal history
    journal_container = st.container(height=400)
    with journal_container:
        for msg in st.session_state.journal_messages:
            with st.chat_message(msg["role"]):
                if msg["role"] == "user" and msg.get("states_detected"):
                    # Show all states detected in this entry
                    states_str = ", ".join([f"{s[1]}" for s in msg["states_detected"]])
                    st.caption(f"States detected: {states_str}")
                st.write(msg["content"])
    
    # Journal input with placeholder showing you can use emojis
    placeholder_text = f"What's on your mind? (Current: {st.session_state.current_state}) Use emojis like 🌀😤⚡ to track state changes..."
    journal_input = st.chat_input(placeholder_text)
    
    if journal_input:
        # Detect ALL mental states in the message
        states_detected = detect_all_states_in_text(journal_input, st.session_state.mental_states)
        
        # If no states detected, use current state
        if not states_detected:
            states_detected = [(0, st.session_state.current_state)]
        
        # Create journal entry with all detected states
        journal_entry = {
            "role": "user",
            "content": journal_input,
            "states_detected": states_detected,
            "primary_state": states_detected[0][1] if states_detected else st.session_state.current_state,
            "timestamp": datetime.now().isoformat()
        }
        
        st.session_state.journal_messages.append(journal_entry)
        st.session_state.all_journal_entries.append(journal_entry)
        save_journal_entry(journal_entry)
        
        # Update current state to the last detected state
        if states_detected:
            st.session_state.current_state = states_detected[-1][1]
        
        # Acknowledgment showing all states detected
        if len(states_detected) > 1:
            states_names = [f"{emoji} ({st.session_state.mental_states.get(emoji, {}).get('name', 'unknown')})" 
                           for _, emoji in states_detected]
            response = f"✓ Captured. I see you moved through these states: {' → '.join(states_names)}"
        else:
            emoji = states_detected[0][1]
            state_name = st.session_state.mental_states.get(emoji, {}).get('name', 'unknown')
            response = f"✓ Captured in {emoji} ({state_name}) state."
        
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
            f"States {e.get('states_detected', [e.get('primary_state', '')])} at {e.get('timestamp', '')}: {e.get('content', '')}" 
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

RECENT JOURNAL ENTRIES (notice the state transitions):
{journal_context}

YOUR ROLE AS THE MIRROR:
1. Reflect their patterns back clearly
2. Notice state TRANSITIONS in journal entries (e.g., 🧠→🌀→😤 shows a degradation pattern)
3. Point out recurring sequences of states
4. Help them see what triggers state changes
5. Mirror their communication style
6. Don't try to fix - just reflect clearly what you observe
7. Pay attention to multi-state entries - they reveal real-time emotional shifts

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
        # Count all states including transitions
        state_counts = {}
        state_transitions = {}
        
        for entry in st.session_state.all_journal_entries:
            states = entry.get('states_detected', [])
            if not states and entry.get('primary_state'):
                states = [(0, entry.get('primary_state'))]
            
            # Count individual states
            for _, emoji in states:
                state_counts[emoji] = state_counts.get(emoji, 0) + 1
            
            # Track transitions
            if len(states) > 1:
                for i in range(len(states) - 1):
                    transition = f"{states[i][1]}→{states[i+1][1]}"
                    state_transitions[transition] = state_transitions.get(transition, 0) + 1
        
        st.markdown("**Most Common States:**")
        if state_counts:
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
                state_name = st.session_state.mental_states.get(state, {}).get('name', state)
                st.write(f"{state} ({state_name}): {count}x")
        
        if state_transitions:
            st.markdown("**Common Transitions:**")
            for trans, count in sorted(state_transitions.items(), key=lambda x: x[1], reverse=True)[:2]:
                st.caption(f"{trans}: {count}x")
    
    with col3:
        st.markdown("**Recent Patterns:**")
        if st.session_state.patterns:
            recent = st.session_state.patterns[-3:]
            for p in recent:
                st.caption(f"{p.get('state', '')} - {p.get('trigger', '')[:30]}...")
        else:
            st.write("No patterns yet")
    
    st.divider()
    
    # Show recent journal entries with state transitions
    st.markdown("### 📔 Recent Journal Entries")
    if st.session_state.all_journal_entries:
        for entry in reversed(st.session_state.all_journal_entries[-10:]):
            timestamp = entry.get('timestamp', 'Unknown time')[:16] if entry.get('timestamp') else 'Unknown time'
            states = entry.get('states_detected', [])
            if states and len(states) > 1:
                state_flow = " → ".join([s[1] for s in states])
                header = f"{state_flow} - {timestamp}"
            else:
                primary_state = entry.get('primary_state', '?')
                header = f"{primary_state} - {timestamp}"
            
            with st.expander(header):
                st.write(entry.get('content', ''))
                if len(states) > 1:
                    st.caption(f"State journey: {' → '.join([s[1] for s in states])}")
    else:
        st.info("No journal entries yet. Start journaling in the Journal tab!")

# === SIDEBAR ===
with st.sidebar:
    st.header("🧠 Second Brain Status")
    
    if st.session_state.personality:
        st.success(f"✅ {st.session_state.personality.get('name', 'User')}")
    else:
        st.warning("⚠️ No personality set")
    
    st.divider()
    
    st.metric("Total Thoughts", len(st.session_state.all_journal_entries))
    st.metric("Mirror Convos", len(st.session_state.mirror_messages) // 2)
    st.metric("Patterns", len(st.session_state.patterns))
    
    st.divider()
    
    # GitHub save with better feedback
    if st.button("💾 Save to GitHub", type="primary", use_container_width=True):
        with st.spinner("Saving to GitHub..."):
            success, message = save_to_github()
            if success:
                st.success(message)
            else:
                st.error(message)
                st.caption("Try running in terminal:\n`cd ~/secondbrain && git add . && git commit -m 'Update' && git push`")
    
    if st.button("📝 Capture New Patterns", use_container_width=True):
        st.info("Run in terminal:\n`python3 capture_patterns.py`")
    
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.session_state.mental_states = load_mental_states()
        st.session_state.patterns = load_patterns()
        st.session_state.all_journal_entries = load_journal_entries()
        st.success("Data refreshed!")
        st.rerun()
    
    st.divider()
    
    # Quick state indicator
    st.markdown("**Current State**")
    st.info(f"{st.session_state.current_state} - {st.session_state.mental_states.get(st.session_state.current_state, {}).get('name', 'unknown')}")
    
    st.caption("Your Second Brain never forgets")
