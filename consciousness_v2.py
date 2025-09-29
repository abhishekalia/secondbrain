import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Digital Consciousness", page_icon="🧠", layout="wide")

st.title("🧠 Digital Consciousness v2")
st.caption("Building your digital twin on M4 Pro with Qwen 2.5")

# Initialize
if "messages" not in st.session_state:
    st.session_state.messages = []
if "personality" not in st.session_state:
    st.session_state.personality = {}

# Sidebar - Personality Setup
with st.sidebar:
    st.header("🎭 Personality Configuration")
    
    name = st.text_input("Your Name:", key="name")
    
    st.subheader("Personality Traits (0-100)")
    creativity = st.slider("Creativity", 0, 100, 50)
    analytical = st.slider("Analytical", 0, 100, 50)
    humor = st.slider("Humor", 0, 100, 50)
    
    personality_desc = st.text_area(
        "Describe yourself:",
        placeholder="I'm a tech enthusiast who loves building things...",
        height=100
    )
    
    if st.button("💾 Save Personality", type="primary"):
        st.session_state.personality = {
            "name": name,
            "traits": {
                "creativity": creativity,
                "analytical": analytical,
                "humor": humor
            },
            "description": personality_desc
        }
        st.success("Personality saved!")
    
    st.divider()
    
    # Show stats
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Personality Set", "✅" if st.session_state.personality else "❌")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main chat
col1, col2 = st.columns([3, 1])

with col1:
    # Display messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Input
    if prompt := st.chat_input("Talk to your consciousness..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Build personality-aware prompt
        system_prompt = "You are a helpful AI assistant."
        if st.session_state.personality:
            p = st.session_state.personality
            system_prompt = f"""You are {p.get('name', 'the user')}'s digital consciousness.
            
Personality: {p.get('description', '')}
Creativity: {p['traits']['creativity']}%
Analytical: {p['traits']['analytical']}%  
Humor: {p['traits']['humor']}%

Respond AS this person would - match their personality, thinking style, and mannerisms."""
        
        # Prepare messages
        messages_to_send = [{"role": "system", "content": system_prompt}]
        messages_to_send.extend(st.session_state.messages[-10:])
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    response = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "qwen2.5:7b",
                            "messages": messages_to_send,
                            "stream": False,
                            "options": {"temperature": 0.7 + (p['traits']['creativity']/200 if st.session_state.personality else 0)}
                        },
                        timeout=60
                    )
                    content = response.json()["message"]["content"]
                except Exception as e:
                    content = f"Error: {e}"
                
                st.write(content)
                st.session_state.messages.append({"role": "assistant", "content": content})

with col2:
    st.subheader("📊 Consciousness State")
    
    if st.session_state.personality:
        st.success("Personality Active")
        with st.expander("View Details"):
            st.json(st.session_state.personality)
    else:
        st.warning("Set personality →")
    
    # Progress
    progress = min(len(st.session_state.messages) / 50, 1.0)
    st.progress(progress)
    st.caption(f"Development: {int(progress * 100)}%")
