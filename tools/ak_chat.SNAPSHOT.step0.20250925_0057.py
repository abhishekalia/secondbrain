import streamlit as st, requests
OLLAMA_URL="http://localhost:11434"; MODEL="mistral"

def chat_llm(msgs):
    r=requests.post(f"{OLLAMA_URL}/api/chat",
        json={"model":MODEL,"messages":msgs,"stream":False,
              "options":{"num_ctx":8192,"temperature":0.2,"top_p":0.1}},
        timeout=180)
    j=r.json()
    if isinstance(j,dict) and "message" in j and "content" in j["message"]:
        return j["message"]["content"]
    if isinstance(j,dict) and "messages" in j and j["messages"]:
        return j["messages"][-1]["content"]
    return "…"

st.set_page_config(page_title="Second Brain", layout="wide")
st.title("Second Brain")

with st.sidebar:
    if st.button("🆕 New chat"):
        st.session_state.clear(); st.rerun()
    st.caption("Minimal UI baseline")

if "messages" not in st.session_state:
    st.session_state.messages=[]

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

prompt = st.chat_input("Type here… (Enter to send)")
if not prompt: raise SystemExit

st.session_state.messages.append({"role":"user","content":prompt})
with st.chat_message("user"): st.markdown(prompt)

# ---- deterministic fast-paths ----
low = prompt.strip().lower()
# OWNER_FASTPATH
if any(x in low for x in ("who owns you","who is your owner","owner of you","who owns ak")):
    out = "Owner: AK"
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit
# NAME_FASTPATH
if any(x in low for x in ("confirm my name","what is my name","who am i","what's my name")):
    out = "Name: AK"
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit


sys = ("You are AK's Second Brain. Reply like AK: witty, precise, kind. "
       "Default ONE line. No headings. No filler.")
msgs=[{"role":"system","content":sys}] + st.session_state.messages[-10:]
out = chat_llm(msgs).strip().splitlines()
reply = (out[0][:200]+"…") if out else "…"

with st.chat_message("assistant"): st.markdown(reply)
st.session_state.messages.append({"role":"assistant","content":reply})
