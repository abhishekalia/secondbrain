import streamlit as st
import requests
import json
import os
from datetime import datetime

st.set_page_config(page_title="Digital Consciousness", page_icon="🧠", layout="wide")

# Create data directories
os.makedirs("my_data", exist_ok=True)
os.makedirs("my_data/whatsapp", exist_ok=True)

# PERSISTENCE FILES
PERSONALITY_FILE = "my_data/personality_profile.json"
CONVERSATION_HISTORY_FILE = "my_data/conversation_history.json"
TRAINING_DATA_FILE = "my_data/training_data.json"

def load_personality():
    """Load saved personality from file"""
    if os.path.exists(PERSONALITY_FILE):
        with open(PERSONALITY_FILE, 'r') as f:
            return json.load(f)
    return None

def save_personality(personality_data):
    """Save personality to file"""
    with open(PERSONALITY_FILE, 'w') as f:
        json.dump(personality_data, f, indent=2)

def load_training_data():
    """Load all training data for context"""
    training_context = []
    
    # Load thoughts
    if os.path.exists("my_data/raw/thoughts.json"):
        with open("my_data/raw/thoughts.json") as f:
            thoughts = json.load(f)
            for t in thoughts[:5]:  # Use top 5 thoughts
                if isinstance(t, dict):
                    training_context.append(t.get('response', ''))
    
    # Load Q&A pairs
    if os.path.exists("my_data/raw/qa_pairs.json"):
        with open("my_data/raw/qa_pairs.json") as f:
            qa = json.load(f)
            for pair in qa[:5]:  # Use top 5 Q&As
                if isinstance(pair, dict):
                    training_context.append(f"Q: {pair.get('question', '')} A: {pair.get('answer', '')}")
    
    # Load some WhatsApp messages for style
    if os.path.exists("my_data/whatsapp/all_messages.json"):
        with open("my_data/whatsapp/all_messages.json", encoding='utf-8') as f:
            messages = json.load(f)
            # Get a sample of messages for style reference
            training_context.extend(messages[:20] if isinstance(messages, list) else [])
    
    return training_context

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    # Try to load saved personality
    saved_personality = load_personality()
    if saved_personality:
        st.session_state.personality = saved_personality
    else:
        st.session_state.personality = {}

if "training_context" not in st.session_state:
    st.session_state.training_context = load_training_data()

st.title("🧠 Digital Consciousness - Permanent Memory")

# Sidebar
with st.sidebar:
    st.header("🎭 Personality Configuration")
    
    # Check if personality is loaded
    if st.session_state.personality:
        st.success(f"✅ Personality Loaded: {st.session_state.personality.get('name', 'Unknown')}")
        
        # Show current personality
        with st.expander("Current Personality", expanded=False):
            st.json(st.session_state.personality)
        
        if st.button("🔄 Reset Personality"):
            st.session_state.personality = {}
            if os.path.exists(PERSONALITY_FILE):
                os.remove(PERSONALITY_FILE)
            st.rerun()
    else:
        st.warning("⚠️ No personality configured")
    
    st.divider()
    
    # Personality setup form
    with st.form("personality_form"):
        st.subheader("Set/Update Personality")
        
        name = st.text_input("Your Name:", value=st.session_state.personality.get('name', ''))
        
        # Personality sliders
        creativity = st.slider("Creativity", 0, 100, 
                              st.session_state.personality.get('traits', {}).get('creativity', 50))
        analytical = st.slider("Analytical", 0, 100,
                              st.session_state.personality.get('traits', {}).get('analytical', 50))
        humor = st.slider("Humor", 0, 100,
                         st.session_state.personality.get('traits', {}).get('humor', 50))
        casual = st.slider("Casual vs Formal", 0, 100,
                          st.session_state.personality.get('traits', {}).get('casual', 70))
        
        description = st.text_area(
            "Describe yourself:",
            value=st.session_state.personality.get('description', ''),
            placeholder="I'm a tech enthusiast, love building things, communicate casually with friends..."
        )
        
        communication_style = st.text_area(
            "Your communication style:",
            value=st.session_state.personality.get('communication_style', ''),
            placeholder="I use hmm, lol often. Start sentences with 'So' or 'Well'. Mix Hindi/English..."
        )
        
        if st.form_submit_button("💾 Save Personality", type="primary"):
            personality_data = {
                "name": name,
                "traits": {
                    "creativity": creativity,
                    "analytical": analytical,
                    "humor": humor,
                    "casual": casual
                },
                "description": description,
                "communication_style": communication_style,
                "created_at": datetime.now().isoformat()
            }
            
            # Save to session and file
            st.session_state.personality = personality_data
            save_personality(personality_data)
            st.success("✅ Personality saved permanently!")
            st.rerun()
    
    st.divider()
    
    # Stats
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Training Samples", len(st.session_state.training_context))
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# Main chat area
if not st.session_state.personality:
    st.warning("👈 Please configure your personality in the sidebar first!")
    st.info("Your personality will be saved permanently and loaded automatically next time!")
else:
    # Show personality status
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        st.success(f"🧠 Consciousness Active: {st.session_state.personality['name']}")
    with col2:
        st.caption(f"Training samples: {len(st.session_state.training_context)}")
    with col3:
        st.caption(f"Personality saved ✓")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input(f"Talk to {st.session_state.personality['name']}'s consciousness..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Build comprehensive personality prompt
        p = st.session_state.personality
        
        # Create system prompt with training data
        system_prompt = f"""You are {p['name']}'s digital consciousness - an exact replica of their personality and communication style.

CORE PERSONALITY:
{p.get('description', '')}

COMMUNICATION STYLE:
{p.get('communication_style', '')}

PERSONALITY TRAITS:
- Creativity: {p['traits']['creativity']}% ({"very creative" if p['traits']['creativity'] > 70 else "moderately creative" if p['traits']['creativity'] > 30 else "practical"})
- Analytical: {p['traits']['analytical']}% ({"highly analytical" if p['traits']['analytical'] > 70 else "balanced" if p['traits']['analytical'] > 30 else "intuitive"})
- Humor: {p['traits']['humor']}% ({"very humorous" if p['traits']['humor'] > 70 else "occasionally funny" if p['traits']['humor'] > 30 else "serious"})
- Communication: {p['traits']['casual']}% casual ({"very casual/informal" if p['traits']['casual'] > 70 else "balanced" if p['traits']['casual'] > 30 else "formal"})

TRAINING CONTEXT (How {p['name']} actually writes):
{chr(10).join(st.session_state.training_context[:10])}

IMPORTANT: 
- Respond EXACTLY as {p['name']} would - use their phrases, style, and mannerisms
- Match their level of casualness/formality
- Use their typical expressions and communication patterns
- If they mix languages (Hindi/English), you should too
- Be consistent with their personality traits above

You ARE {p['name']}, not an AI assistant. Respond naturally as they would."""
        
        # Prepare messages
        messages_to_send = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        messages_to_send.extend(st.session_state.messages[-10:])
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Accessing consciousness..."):
                try:
                    # Adjust temperature based on personality
                    temperature = 0.5 + (p['traits']['creativity'] / 200)
                    
                    response = requests.post(
                        "http://localhost:11434/api/chat",
                        json={
                            "model": "qwen2.5:7b",
                            "messages": messages_to_send,
                            "stream": False,
                            "options": {
                                "temperature": temperature,
                                "top_p": 0.9,
                                "frequency_penalty": 0.3,  # Reduce repetition
                                "presence_penalty": 0.3    # Encourage variety
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

# Footer
st.divider()
st.caption(f"🧠 Digital Consciousness with Permanent Memory | Qwen 2.5 on M4 Pro")
if st.session_state.personality:
    st.caption(f"Personality Profile: {st.session_state.personality['name']} | Saved permanently ✓")
