import streamlit as st
import google.generativeai as genai
from openai import OpenAI
from duckduckgo_search import DDGS
import time

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NeonOps Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CYBERPUNK CSS (Gemini-Style Layout) ---
st.markdown("""
<style>
    /* Dark Theme Fixes */
    .stApp {
        background-color: #0e0e11;
        color: #e0e0e0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #050507;
        border-right: 1px solid #333;
    }
    
    /* Tool Buttons in Sidebar */
    div.stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        color: #888;
        padding: 10px;
        font-size: 14px;
        transition: 0.2s;
    }
    div.stButton > button:hover {
        color: #00f0ff;
        background: rgba(0, 240, 255, 0.1);
        border-left: 2px solid #00f0ff;
    }
    div.stButton > button:focus {
        color: #fff;
        background: rgba(0, 240, 255, 0.2);
    }

    /* Chat Input Area */
    .stChatInput {
        position: fixed;
        bottom: 30px;
    }
    
    /* Headers */
    h1 span { color: #00f0ff; text-shadow: 0 0 15px rgba(0,240,255,0.5); }
</style>
""", unsafe_allow_html=True)

# --- 3. SESSION STATE (Memory) ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_tool" not in st.session_state:
    st.session_state.current_tool = "🚀 Viral Engine"
if "model_provider" not in st.session_state:
    st.session_state.model_provider = "Google Gemini"

# --- 4. HELPER FUNCTIONS ---
def search_web(query):
    """Real-time web search using DuckDuckGo"""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
            return str(results)
    except:
        return "No live data available."

def get_api_key(provider):
    """Securely fetch keys from Streamlit Secrets"""
    try:
        if provider == "Google Gemini":
            return st.secrets["GEMINI_API_KEY"]
        elif provider == "OpenRouter":
            return st.secrets["OPENROUTER_API_KEY"]
    except:
        return None

# --- 5. SIDEBAR (Tool Selection) ---
with st.sidebar:
    st.markdown("### ⚡ NEON OPS")
    
    # Model Selector
    st.session_state.model_provider = st.selectbox(
        "AI Model Core",
        ["Google Gemini", "OpenRouter"]
    )
    
    st.markdown("---")
    st.markdown("### 🛠️ TOOLS")
    
    # Tool Menu
    tools = [
        "🚀 Viral Engine", "🧵 Thread Weaver", "🛡️ Token Auditor", 
        "🕵️ Rug Detective", "🌍 X Trend Scout", "🔬 Market Intel",
        "🧠 Psych Coach", "🪂 Airdrop Farmer", "📜 Code Breaker",
        "🖼️ NFT Forge", "💬 Community Bot", "📹 YT Director"
    ]
    
    for tool in tools:
        if st.button(tool):
            st.session_state.current_tool = tool
            st.session_state.messages = [] # Clear chat on tool switch
            st.rerun()

    st.markdown("---")
    st.caption("v2.0 | Connected")

# --- 6. MAIN CHAT INTERFACE ---

# Header
tool_name = st.session_state.current_tool
st.markdown(f"<h1>{tool_name} <span>AI</span></h1>", unsafe_allow_html=True)

# Persona Logic
personas = {
    "🚀 Viral Engine": "You are a Viral Content Creator. Write 3 punchy, high-engagement tweets about the user's topic. Use emojis.",
    "🧵 Thread Weaver": "You are a Thread Master. Write a compelling Twitter thread (Hook + 5 tweets) about the topic.",
    "🛡️ Token Auditor": "You are a Smart Contract Auditor. Analyze the contract code or address for risks, honeypots, and tax settings.",
    "🕵️ Rug Detective": "You are a Cynical DeFi Detective. Rate the 'Rug Probability' (0-100%) of the project based on red flags.",
    "🌍 X Trend Scout": "You are a Web3 Trend Hunter. I will provide live search data. Summarize the current meta/narrative on Crypto Twitter.",
    "🔬 Market Intel": "You are a Financial Analyst. Provide a professional report on the project's utility, sentiment, and risks.",
    "🧠 Psych Coach": "You are a Stoic Trading Psychologist. Give stern but helpful advice to manage FOMO and panic selling.",
    "🪂 Airdrop Farmer": "You are an Airdrop Strategist. Provide a step-by-step checklist to farm the specific project.",
    "📜 Code Breaker": "You are a Senior Solidity Dev. Explain the code snippet simply and highlight vulnerabilities.",
    "🖼️ NFT Forge": "You are a Metadata Engine. Generate a clean JSON structure for an NFT collection.",
    "💬 Community Bot": "You are a Community Manager. Write a polite, hype-building reply to a user question.",
    "📹 YT Director": "You are a YouTube Strategist. Write a video Hook, Intro, and Outline."
}
system_prompt = personas.get(tool_name, "You are a helpful AI.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input Handler
if prompt := st.chat_input(f"Enter input for {tool_name}..."):
    # 1. Add User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            
            # Check for Live Data Tools
            web_context = ""
            if tool_name in ["🌍 X Trend Scout", "🔬 Market Intel"]:
                search_data = search_web(prompt + " crypto news analysis")
                web_context = f"\n\nLIVE WEB DATA:\n{search_data}\n\n"

            full_prompt = f"SYSTEM: {system_prompt}\n{web_context}\nUSER: {prompt}"
            
            response_text = "Error: Configuration Failed."
            api_key = get_api_key(st.session_state.model_provider)
            
            if not api_key:
                response_text = "⚠️ Error: API Key not found in Secrets."
            else:
                try:
                    # GEMINI ENGINE
                    if st.session_state.model_provider == "Google Gemini":
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(full_prompt)
                        response_text = response.text
                        
                    # OPENROUTER ENGINE
                    elif st.session_state.model_provider == "OpenRouter":
                        client = OpenAI(
                            base_url="https://openrouter.ai/api/v1",
                            api_key=api_key,
                        )
                        # Auto-select model (DeepSeek V3 is standard for OR)
                        or_model = "deepseek/deepseek-chat"
                        completion = client.chat.completions.create(
                            model=or_model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt + web_context}
                            ]
                        )
                        response_text = completion.choices[0].message.content
                        
                except Exception as e:
                    response_text = f"⚠️ API Error: {str(e)}"

            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
