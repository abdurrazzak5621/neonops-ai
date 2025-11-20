# app.py
"""
NeonOpsAI Streamlit frontend.
 - Connects to realtime_server WebSocket to receive X feed and model streaming tokens
 - Gemini-style chat UI with model selection dropdown
 - Image generation tab (simple stub)
 - Uses .env for API keys and SERVER_HOST/PORT
Run after starting the server:
  1) uvicorn realtime_server:app --reload --port 8000
  2) streamlit run app.py
"""

import os
import time
import json
import uuid
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = os.getenv("SERVER_PORT", "8000")
WS_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"
HTTP_RUN_MODEL = f"http://{SERVER_HOST}:{SERVER_PORT}/run_model"

st.set_page_config(page_title="NeonOpsAI", layout="wide")

# Neon styling
st.markdown("""
<style>
body { background: linear-gradient(180deg,#020204 0%, #071422 100%); color: #dbeafe; }
.header {
  display:flex; align-items:center; justify-content:space-between;
  padding: 12px 18px; border-radius:12px;
  background: linear-gradient(90deg, rgba(0,234,255,0.04), rgba(110,0,255,0.02));
  border: 1px solid rgba(0,234,255,0.08);
}
.title { font-size:28px; color:#00eaff; font-weight:800; }
.tagline { color:#a7f3d0; opacity:0.9; }
.card { background:#07121a; padding:12px; border-radius:10px; border:1px solid #072b33; }
.model-badge { background:#001f22; color:#7fffd4; padding:6px 8px; border-radius:6px; }
.chat-box { background:black; border-radius:8px; padding:12px; }
.stream-token { color:#00eaff; font-weight:600; display:inline-block; }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3,1])
with col1:
    st.markdown('<div class="header"><div><div class="title">NeonOpsAI</div><div class="tagline">Command Center for Web3 Creators — 100% Free. No Wallet Connection Required. Just Paste & Scan.</div></div></div>', unsafe_allow_html=True)

# Sidebar controls
with st.sidebar:
    st.markdown("### Settings")
    model_choice = st.selectbox("Model", ["DeepSeek", "Claude", "OpenAI (fallback)"])
    st.markdown("---")
    st.write("Realtime X feed")
    x_query = st.text_input("X Query (for server polling)", value="#web3")
    st.write("WebSocket server")
    st.write(f"{WS_URL}")
    if st.button("Reconnect WebSocket"):
        st.experimental_rerun()

# Tabs: Home, Chat, Image
tabs = st.tabs(["Home", "Chat", "Image"])
# HOME
with tabs[0]:
    st.markdown("## Welcome to NeonOpsAI")
    st.markdown("Free AI toolkit for X creators. Click Chat to open Gemini-style interface.")
    # show tiles for tools
    cols = st.columns(3)
    tools = ["SEO Writer", "YouTube Script Maker", "AdSense Writer", "X Viral Post Maker", "Image Idea Generator", "AI Research Assistant"]
    for i, t in enumerate(tools):
        with cols[i % 3]:
            if st.button(t):
                st.session_state.setdefault("selected_tool", t)
                st.experimental_set_query_params(tool=t)
                st.experimental_rerun()

# CHAT - main interface
with tabs[1]:
    st.markdown("## Gemini-style Chat")
    selected_tool = st.session_state.get("selected_tool", "AI Chat - DeepSeek")
    col_main, col_side = st.columns([3,1])
    with col_side:
        st.markdown("### Tools")
        for t in ["AI Chat - DeepSeek", "AI Chat - Claude", "SEO Writer", "YouTube Script Maker", "Image Idea Generator"]:
            if st.button(t):
                selected_tool = t
                st.session_state["selected_tool"] = t
                st.experimental_rerun()
        st.markdown("---")
        st.markdown("### Real-time X")
        st.write("Live updates below (via WebSocket)")
        st.empty()  # spot for feed from component

    with col_main:
        st.markdown(f"### Active — {selected_tool}  <span class='model-badge'>{model_choice}</span>", unsafe_allow_html=True)
        chat_placeholder = st.empty()
        # a visible area for streaming tokens
        stream_box = st.empty()

        # chat history kept in session
        if "chats" not in st.session_state:
            st.session_state.chats = {}
        if selected_tool not in st.session_state.chats:
            st.session_state.chats[selected_tool] = []

        # show previous messages
        for m in st.session_state.chats[selected_tool]:
            role = m.get("role")
            text = m.get("text")
            if role == "user":
                st.markdown(f"**You:** {text}")
            else:
                st.markdown(f"**NeonOpsAI:** {text}")

        user_input = st.text_input("Ask NeonOpsAI...", key="user_input")
        if st.button("Send"):
            if not user_input:
                st.warning("Write something first.")
            else:
                # save user message
                st.session_state.chats[selected_tool].append({"role": "user", "text": user_input})
                chat_id = str(uuid.uuid4())[:8]
                # send run_model HTTP request (non-stream) and also open streaming via ws
                try:
                    # start websocket-driven streaming by sending a ws message (embedded component will do that)
                    # we also call HTTP endpoint to obtain full text as fallback
                    resp = requests.post(HTTP_RUN_MODEL, json={"model": model_choice.lower(), "prompt": user_input}, timeout=30)
                    if resp.status_code == 200:
                        text = resp.json().get("text", "")
                    else:
                        text = f"Model endpoint error {resp.status_code}: {resp.text}"
                except Exception as e:
                    text = f"Error calling model endpoint: {e}"

                # append final text to chat (the streaming JS will show tokens live)
                st.session_state.chats[selected_tool].append({"role": "assistant", "text": text})
                st.experimental_rerun()

        # Streaming + WebSocket client embedded in component
        # This small HTML/JS component connects to server WS and listens for messages.
        ws_html = f"""
        <div id="neonops_feed" style="background:#00121a;border-radius:8px;padding:8px;height:240px;overflow:auto;border:1px solid rgba(0,234,255,0.06)"></div>
        <script>
        const wsUrl = "{WS_URL}";
        const el = document.getElementById('neonops_feed');
        let ws = new WebSocket(wsUrl);
        ws.onopen = () => {{
            console.log("ws open");
            // optionally, request model runs by sending JSON message, e.g.:
            // ws.send(JSON.stringify({{action:"run_model", model:"{model_choice.lower()}", prompt:"hello", session_id:"s1"}}));
        }};
        ws.onmessage = (evt) => {{
            try {{
                const data = JSON.parse(evt.data);
                if(data.type === "x_feed") {{
                    const q = data.query;
                    const items = data.items || [];
                    const h = document.createElement('div');
                    h.innerHTML = `<b style="color:#7fffd4">X feed — ${q}</b><br/>` + items.map(i => '<div style="padding:6px 0;border-bottom:1px dashed rgba(255,255,255,0.02)">' + i + '</div>').join('');
                    el.prepend(h);
                }} else if (data.type === "model_stream") {{
                    const token = data.token || '';
                    // append token with neon styling
                    const span = document.createElement('span');
                    span.className = 'stream-token';
                    span.innerText = token;
                    el.prepend(span);
                    el.prepend(document.createElement('br'));
                }} else if (data.type === "model_complete") {{
                    const m = document.createElement('div');
                    m.innerHTML = `<b style="color:#00eaff">Model complete:</b><div>${data.text}</div><hr/>`;
                    el.prepend(m);
                }} else if (data.type === "model_error") {{
                    const m = document.createElement('div');
                    m.innerHTML = `<b style="color:#ff6b6b">Model error:</b> ${data.error}`;
                    el.prepend(m);
                }}
            }} catch(e) {{
                console.error("WS msg parse error", e);
            }}
        }};
        ws.onclose = () => console.log("ws closed");
        </script>
        """
        components.html(ws_html, height=280)

# IMAGE tab (simple UI)
with tabs[2]:
    st.markdown("## Image Generation")
    prompt = st.text_input("Describe the image you want (no humans):", value="Nature sunrise over mountains, cinematic, 16:9")
    if st.button("Generate Image"):
        # This is a stub. Wire to your image API (DeepSeek/StableDiffusion/OpenAI) here.
        st.info("Image generation stub: wire your image generation API here.")
        st.image("https://via.placeholder.com/800x450.png?text=Image+Generation+Stub", caption="Generated (stub)")

