# NeonOpsAI - Streamlit + FastAPI Hybrid App
# Everything in one file for non-technical setup
# NOTE: This file is simplified so you can run it directly.

import streamlit as st
import requests
import os
import threading
import time
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.websockets import WebSocket
import uvicorn

# -----------------------
# LOAD API KEYS
# -----------------------
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# -----------------------
# FASTAPI BACKEND (for real-time X.com polling)
# -----------------------
fastapi_app = FastAPI()
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

latest_x_data = "Initializing feed..."

# Fake real-time polling for demo (replace with genuine API later)
def poll_x_feed():
    global latest_x_data
    while True:
        latest_x_data = f"🔥 LIVE FEED UPDATE — Time: {time.strftime('%H:%M:%S')}"
        time.sleep(5)

threading.Thread(target=poll_x_feed, daemon=True).start()

@fastapi_app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    while True:
        await ws.send_text(latest_x_data)
        time.sleep(1)

# -----------------------
# START FASTAPI IN BACKGROUND
# -----------------------
def start_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8502)

threading.Thread(target=start_fastapi, daemon=True).start()

# -----------------------
# DEEPSEEK + CLAUDE CHAT FUNCTIONS
# -----------------------
def chat_claude(prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data).json()
    return response["content"][0]["text"]

def chat_deepseek(prompt):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data).json()
    return response["choices"][0]["message"]["content"]

# -----------------------
# STREAMLIT FRONTEND
# -----------------------
st.set_page_config(page_title="NeonOpsAI", layout="wide")
st.markdown(
    """
    <h1 style='text-align:center; color:#00f2ff;'>⚡ NeonOpsAI</h1>
    <p style='text-align:center; color:#fff;'>Command Center for Web3 Creators<br>100% Free. No Wallet Connection Required. Just Paste & Scan.</p>
    """,
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.title("⚡ NeonOpsAI Tools")
model_choice = st.sidebar.selectbox("Choose Model", ["Claude", "DeepSeek"])

st.sidebar.markdown("---")
st.sidebar.markdown("**🚀 Real-time X Feed**")
st.sidebar.text(latest_x_data)

# Chat Interface
st.subheader("💬 Chat Interface")
user_input = st.text_input("Ask anything…")

if user_input:
    with st.spinner("Thinking..."):
        if model_choice == "Claude":
            answer = chat_claude(user_input)
        else:
            answer = chat_deepseek(user_input)

    st.markdown(f"### 🤖 Response:\n{answer}")

# Real-time feed display
st.markdown("---")
st.subheader("🔥 Live X Feed (Demo)")
st.text(latest_x_data)

# End of file
