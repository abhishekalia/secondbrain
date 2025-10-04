import streamlit as st
import requests
import json
import os
from datetime import datetime

st.set_page_config(page_title="Digital Twin - Pattern Recognition", page_icon="🧠", layout="wide")

# Load everything
def load_mental_states():
    if os.path.exists("my_data/mental_states.json"):
        with open("my_data/mental_states.json") as f:
            return json.load(f)
    return {}

def load_patterns():
    patterns = []
    pattern_dir = "my_data/patterns"
    if os.path.exists(pattern_dir):
        for file in os.listdir(pattern_dir):
            if file.endswith('.json'):
                with open(os.path.join(pattern_dir, file)) as f:
                    patterns.extend(json.load(f))
    return patterns

def load_personality():
    if os.path.exists("my_data/personality_profile.json"):
        with open("my_data/personality_profile.json") as f:
            return json.load(f)
    return {}

# Initialize
if "mental_states" not in st.session_state:
    st.session_state.mental_states = load_mental_states()
if "patterns" not in st.session_state:
    st.session_state.patterns = load_patterns()
if "personality" not in st.session_state:
    st.session_state.personality = load_personality()
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🧠 Digital Twin - Pattern-Aware Consciousness")

# Sidebar
with st.sidebar:
    st.header("🌀 Mental State")
    
    if st.session_state.mental_states:
        current_state = st.selectbox(
            "Current state:",
            options=list(st.session_state.mental_states.keys()),
            format_func=lambda x: f"{x} {st.session_state.mental_states[x]['name']}"
        )
        
        state_info = st.session_state.mental_states.get(current_state, {})
        st.info(state_info.get('description', ''))
    
    st.divider()
    
    # Statistics
    st.metric("Patterns Captured", len(st.session_state.patterns))
    st.metric("Mental States", len(st.session_state.mental_states))
    
    if st.session_state.personality:
        st.success(f"✅ Personality: {st.session_state.personality.get('name', 'Loaded')}")
    
    if st.button("🔄 Refresh Patterns"):
        st.session_state.patterns = load_patterns()
        st.rerun()

# Main chat area
tab1, tab2, tab3 = st.tabs(["💬 Mirror Chat", "🔍 Pattern Analysis", "🧬 Your Patterns"])

with tab1:
    # Display conversation
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user" and "state" in message:
                st.caption(f"Mental state: {message['state']}")
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Share what's on your mind..."):
        # Add message with mental state
        user_msg = {
            "role": "user",
            "content": prompt,
            "state": current_state if 'current_state' in locals() else "🧠"
        }
        st.session_state.messages.append(user_msg)
        
        with st.chat_message("user"):
            if 'current_state' in locals():
                st.caption(f"Mental state: {current_state}")
            st.write(prompt)
        
        # Build comprehensive system prompt
        personality = st.session_state.personality
        patterns_context = json.dumps(st.session_state.patterns[-5:], indent=2) if st.session_state.patterns else ""
        
        system_prompt = f"""You are {personality.get('name', 'the user')}'s digital twin - a pattern recognition system that mirrors their actual thinking.

PERSONALITY PROFILE:
{json.dumps(personality, indent=2)}

MENTAL STATES I RECOGNIZE:
{json.dumps(st.session_state.mental_states, indent=2)}

RECENT PATTERNS I'VE LEARNED:
{patterns_context}

IMPORTANT INSTRUCTIONS:
1. When you see a mental state emoji, acknowledge and respond to that state
2. Mirror their ACTUAL patterns (from the patterns above), not ideal behaviors
3. Reflect back what you observe about their thinking patterns
4. Help them see their loops clearly, without judgment
5. Speak in their voice, using their communication style
6. If you recognize a pattern forming, gently point it out

Current mental state: {current_state if 'current_state' in locals() else 'unknown'}

Be a mirror, not a coach. Show them their patterns, don't try to fix them."""
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Pattern matching..."):
                try:
                    messages_to_send = [
                        {"role": "system", "content": system_prompt}
                    ]
                    messages_to_send.extend([
                        {"role": m["role"], "content": m["content"]} 
                        for m in st.session_state.messages[-10:]
                    ])
                    
                    response = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "qwen2.5:7b",
                            "messages": messages_to_send,
                            "stream": False,
                            "options": {
                                "temperature": 0.7,
                                "top_p": 0.9
                            }
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        content = response.json()["message"]["content"]
                    else:
                        content = "Connection error. Make sure Ollama is running."
                except Exception as e:
                    content = f"Error: {str(e)}"
                
                st.write(content)
                st.session_state.messages.append({"role": "assistant", "content": content})

with tab2:
    st.header("🔍 Pattern Analysis")
    
    if st.session_state.patterns:
        # Group patterns by state
        patterns_by_state = {}
        for p in st.session_state.patterns:
            state = p.get('state', 'unknown')
            if state not in patterns_by_state:
                patterns_by_state[state] = []
            patterns_by_state[state].append(p)
        
        # Show patterns by mental state
        for state, patterns in patterns_by_state.items():
            with st.expander(f"{state} - {len(patterns)} patterns"):
                for p in patterns:
                    st.write(f"**Trigger:** {p.get('trigger', '')}")
                    st.write(f"**Pattern:** {p.get('pattern', '')}")
                    st.write(f"**Typical Response:** {p.get('typical_response', '')}")
                    st.write("---")
    else:
        st.info("No patterns captured yet")

with tab3:
    st.header("🧬 Your Captured Patterns")
    
    if st.session_state.patterns:
        for idx, pattern in enumerate(reversed(st.session_state.patterns[-10:]), 1):
            with st.expander(f"Pattern {idx}: {pattern.get('state', '')} - {pattern.get('timestamp', '')[:10]}"):
                st.write(f"**Mental State:** {pattern.get('state', '')}")
                st.write(f"**What was happening:** {pattern.get('pattern', '')}")
                st.write(f"**Trigger:** {pattern.get('trigger', '')}")
                st.write(f"**How you typically handle it:** {pattern.get('typical_response', '')}")
                st.write(f"**Ideal response:** {pattern.get('ideal_response', '')}")
                st.caption(f"Captured: {pattern.get('timestamp', '')}")
    
    if st.button("📝 Capture More Patterns"):
        st.info("Run `python3 capture_patterns.py` in terminal to capture more patterns")
