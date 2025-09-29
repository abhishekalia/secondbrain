# Create the Streamlit app
with open("app.py", "w") as f:
    f.write('''import streamlit as st
import requests

st.title("🧠 Your Digital Consciousness")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Talk to your digital brain..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen2.5:7b",
                    "messages": st.session_state.messages[-5:],
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                ai_text = response.json()["message"]["content"]
            else:
                ai_text = "Error: Could not connect to Ollama"
        except Exception as e:
            ai_text = f"Error: {e}"
        
        st.write(ai_text)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})
''')

print("✅ Created app.py")
print("\n🚀 Now run: streamlit run app.py")
