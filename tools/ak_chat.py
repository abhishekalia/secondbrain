# tools/ak_chat.py
import streamlit as st
import traceback

from core.llm import chat, LLMError
from core.prompt import build_messages
try:
    from core import memory
except Exception:
    memory = None

st.set_page_config(page_title="AKtivate.ai", page_icon="⚡", layout="wide")
st.title("AK — Second Brain (Local)")

with st.sidebar:
    st.caption("AKtivate.ai • Local Jarvis")
    if st.button("New Chat"):
        st.session_state["history"] = []

history = st.session_state.setdefault("history", [])

for role, content in history:
    with st.chat_message(role):
        st.markdown(content)

user_text = st.chat_input("Type… (one-liners preferred)")
if not user_text:
    st.stop()

history.append(("user", user_text))
with st.chat_message("user"):
    st.markdown(user_text)

ctx_snippets = []
if memory:
    try:
        last_j = memory.get_last_journal(embedder=None, k=1)
        if last_j:
            ctx_snippets.append(f"Last journal: {last_j[0][:400]}")
    except Exception:
        pass

trunc = history[-16:]
user_as_text = trunc[-1][1] if trunc else user_text
msgs = build_messages(user_as_text, context_snippets=ctx_snippets)

try:
    reply = chat(msgs)
except LLMError as e:
    reply = f"LLM error: {e}\n\n**Next step:** run the curl health check and ensure Ollama is serving."
except Exception:
    reply = "Unhandled error:\n\n```\n" + traceback.format_exc() + "\n```"

with st.chat_message("assistant"):
    st.markdown(reply)
history.append(("assistant", reply))


