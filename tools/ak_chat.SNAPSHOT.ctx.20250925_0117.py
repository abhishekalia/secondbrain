import streamlit as st, requests, re, json

def _set_last_detail(text:str):
    st.session_state['last_detail'] = text or ''

def _get_last_detail():
    return st.session_state.get('last_detail','')


def _one_line(x):
    return ' '.join(str(x).splitlines())

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
low = prompt.strip().lower()  # ensure available for all fast-path handlers


# ---- deterministic fast-paths ----
# MORE_FASTPATH
if low in ("more","tell me more","expand","details","expand last"):
    detail = _get_last_detail() or st.session_state.get("last_full","")
    out = detail if detail else "No prior detail to expand."
    with st.chat_message("assistant"): st.markdown(out if len(out) <= 2000 else out[:2000] + "\n…")
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit


# JOURNAL_DATE_KEYWORD_FASTPATH
m = re.search(r'^journal\s+on[:\s]+([^\n]+?)\s+(?:keyword|about|with)[:\s]+(.+)$', low)
if m:
    raw_date, kw = m.group(1).strip(), m.group(2).strip().lower()
    # normalize date: YYYY-MM-DD or "Sep 21"
    from datetime import datetime as _dt
    date_key = None
    for fmt in ("%Y-%m-%d","%b %d","%B %d"):
        try:
            dt = _dt.strptime(raw_date, fmt)
            year = dt.year if "%Y" in fmt else _dt.now().year
            date_key = f"{year:04d}-{dt.month:02d}-{dt.day:02d}"
            break
        except Exception:
            pass
    rows = []
    memlog = Path.home()/ "ak"/ "memories"/ "memories.jsonl"
    try:
        for line in memlog.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                if rec.get("type") == "journal":
                    ts = str(rec.get("timestamp",""))
                    txt = (rec.get("text") or "")
                    if (not date_key or ts.startswith(date_key)) and (kw in txt.lower()):
                        rows.append((ts, txt.strip()))
            except Exception:
                pass
    except FileNotFoundError:
        rows = []
    rows.sort(key=lambda x: x[0])
    if not rows:
        out = "No matching journal entries."
        details_store = ''
    else:
        bullets = []
        for ts, txt in rows[-5:]:
            bullets.append(f"- {ts} — {_one_line(txt)[:160]}")
        out = f"Matches for '{kw}' on {raw_date}:\n" + "\n".join(bullets)
        details_store = "\n\n".join([f"{ts}\n{txt}" for ts, txt in rows[-5:]])
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    
    _set_last_detail(details_store)
raise SystemExit



# LAST_JOURNAL_FASTPATH
if low.startswith("last journal") or low == "last journal":
    memlog = Path.home()/ "ak"/ "memories"/ "memories.jsonl"
    rows=[]
    try:
        for line in memlog.read_text(encoding="utf-8").splitlines():
            try:
                rec=json.loads(line)
                if rec.get("type")=="journal":
                    rows.append((rec.get("timestamp",""), (rec.get("text") or "").strip()))
            except Exception:
                pass
    except FileNotFoundError:
        rows=[]
    rows.sort(key=lambda x: x[0])
    out = "No journal entries found." if not rows else f"Last journal ({rows[-1][0]}):\n- {_one_line(rows[-1][1])[:160]}"
    _set_last_detail(rows[-1][1] if rows else '')
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit


# VALUES_FASTPATH
if any(x in low for x in ("what are my values","tell me my values","my values")):
    f = Path.home()/ "ak"/ "data"/ "identity"/ "values.md"
    if not f.exists():
        out = "(no values.md file)"
    else:
        lines = [ln.strip(" -*") for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out = "\n".join("- "+ln[:120]+("…" if len(ln)>120 else "") for ln in lines[:6]) if lines else "(empty)"
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit


# BELIEFS_FASTPATH
if any(x in low for x in ("what are my beliefs","tell me my beliefs","my beliefs","what do i believe")):
    f = Path.home()/ "ak"/ "data"/ "identity"/ "beliefs.md"
    if not f.exists():
        out = "(no beliefs.md file)"
    else:
        lines = [ln.strip(" -*") for ln in f.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out = "\n".join("- "+ln[:120]+("…" if len(ln)>120 else "") for ln in lines[:6]) if lines else "(empty)"
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit


# WHOIS_FASTPATH
if any(x in low for x in ("who is ak","tell me about ak","tell me more about ak")):
    # detect "in N lines"
    m = re.search(r'\b(?:in|within)\s+(\d+)\s+lines?\b', low) or re.search(r'\b(\d+)\s+lines?\b', low)
    n = int(m.group(1)) if m else None
    name, role = "AK", "Artist"
    if n and n > 1:
        bullets = [
            f"- {name} — {role}; builds AKtivate.ai (Second Brain).",
            "- Voice: witty, precise, kind; bias to action.",
            "- Values: speed, integrity, impact; freedom/purpose/curiosity.",
            "- Heuristic: act fast; test & adjust; prefer reversible steps.",
            "- Identity focus: Artist; blends creativity with systems."
        ][:n]
        out = "\n".join(bullets)
    elif "more" in low:
        out = f"- {name} — {role}; builds AKtivate.ai (Second Brain).\n- Voice: witty, precise, kind; bias to action."
    else:
        out = f"{name} — {role}; builds AKtivate.ai (Second Brain)."
    with st.chat_message("assistant"): st.markdown(out)
    st.session_state.messages.append({"role":"assistant","content":out})
    raise SystemExit

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
