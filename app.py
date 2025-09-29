import streamlit as st
import requests

st.title("🧠 Your Digital Consciousness")
st.sidebar.write("Powered by Qwen 2.5 on M4 Pro")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Talk to your digital brain..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "qwen2.5:7b",
                        "messages": st.session_state.messages[-5:],
                        "stream": False
                    }
                )
                content = response.json()["message"]["content"]
            except:
                content = "Error: Make sure Ollama is running"
            
            st.write(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
