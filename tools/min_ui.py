import streamlit as st, json, urllib.request
st.title('LLM Smoke')

q = st.text_input('Say:', 'hi')

if st.button('Send'):
    req = urllib.request.Request(
        'http://localhost:11434/api/chat',
        data=json.dumps({
            'model':'mistral:latest',
            'messages':[{'role':'user','content':q}],
            'stream': False
        }).encode('utf-8'),
        headers={'Content-Type':'application/json'},
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            st.code(json.loads(r.read().decode('utf-8'))['message']['content'])
    except Exception as e:
        st.error(str(e))

