import streamlit as st
import os
from openai import OpenAI
from anthropic import Anthropic
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NeonOpsAI | Web3 Command Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME CONFIGURATION (DEGEN TOOLKIT STYLE) ---
# Colors extracted from the reference site
NEON_GREEN = "#00ff9d"
NEON_BLUE = "#00f3ff"
BG_DARK = "#0a0a0a"
CARD_BG = "#111111"
TEXT_GRAY = "#888888"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&display=swap');

    /* --- GLOBAL RESET --- */
    .stApp {{
        background-color: {BG_DARK};
        font-family: 'Space Mono', monospace;
    }}
    
    /* --- TYPOGRAPHY --- */
    h1, h2, h3 {{
        color: white !important;
        font-family: 'Space Mono', monospace !important;
        letter-spacing: -1px;
    }}
    
    h1 span {{
        background: -webkit-linear-gradient(45deg, {NEON_GREEN}, {NEON_BLUE});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}

    /* --- SIDEBAR --- */
    [data-testid="stSidebar"] {{
        background-color: #050505;
        border-right: 1px solid #222;
    }}
    
    /* --- CARD GRID STYLING (MATCHING DEGEN TOOLKIT) --- */
    div.stButton > button {{
        background-color: {CARD_BG};
        color: white;
        border: 1px solid #222;
        border-radius: 12px;
        height: 140px;
        width: 100%;
        transition: all 0.2s ease-in-out;
        display: flex;
        flex-direction: column;
        align-items: flex-start; /* Align text left like the site */
        justify-content: flex-start;
        padding: 20px;
        text-align: left;
    }}
    
    div.stButton > button:hover {{
        border-color: {NEON_GREEN};
        box-shadow: 0 0 20px rgba(0, 255, 157, 0.1);
        transform: translateY(-2px);
        color: {NEON_GREEN};
    }}

    div.stButton > button p {{
        font-size: 14px;
        line-height: 1.4;
    }}

    /* --- CHAT INTERFACE --- */
    .stChatMessage {{
        background-color: {CARD_BG};
        border: 1px solid #222;
    }}
    
    [data-testid="stChatInput"] {{
        background-color: {CARD_BG};
        border: 1px solid #333;
        color: white;
    }}

    /* --- ALERTS & LOGS --- */
    .stAlert {{
        background-color: #1a1a1a;
        color: {NEON_GREEN};
        border: 1px solid {NEON_GREEN};
    }}
    
</style>
""", unsafe_allow_html=True)

# --- SYSTEM PROMPTS & TOOL CONFIG ---
TOOLS = {
    "SECURITY & RISK": {
        "Token Auditor": {"icon": "🛡️", "desc": "Scan contracts for vulnerabilities.", "prompt": "You are a Web3 Security Auditor. Analyze smart contracts and tokenomics for vulnerabilities, honey-pots, and centralization risks."},
        "Rug Detective": {"icon": "🕵️", "desc": "Analyze team & liquidity risks.", "prompt": "You are a Rug Pull Detective. Analyze project roadmaps, team behavior, and liquidity setups for signs of scams."},
    },
    "CONTENT CREATION": {
        "Viral Engine": {"icon": "🚀", "desc": "Generate viral X/Twitter posts.", "prompt": "You are a Viral Twitter/X Ghostwriter. Write punchy, engaging, and slightly controversial tweets about crypto."},
        "Thread Weaver": {"icon": "🧵", "desc": "Create deep-dive threads.", "prompt": "You are a Master Thread Writer. Create educational or narrative Twitter threads. Start with a killer hook."},
    },
    "GROWTH & STRATEGY": {
        "X Scout": {"icon": "🔭", "desc": "Analyze profiles for growth.", "prompt": "You are a Social Media Analyst. Analyze user profiles, bios, and content strategies to suggest growth hacks."},
        "Airdrop Farmer": {"icon": "🚜", "desc": "Farming strategies & guides.", "prompt": "You are an Airdrop Strategy Expert. Provide step-by-step guides to farming potential airdrops."},
        "SEO Booster": {"icon": "📈", "desc": "Web3 keyword optimization.", "prompt": "You are a Web3 SEO Specialist. Optimize content for crypto keywords and meta tags."},
    },
    "DEVELOPMENT": {
        "Code Breaker": {"icon": "💻", "desc": "Explain complex Solidity.", "prompt": "You are a Senior Solidity Developer. Explain complex smart contract code in simple terms."},
        "Data Decoder": {"icon": "🧩", "desc": "Simplify whitepapers.", "prompt": "You are a Technical Translator. Take complex whitepapers and simplify it for a 5-year-old (ELI5)."},
    },
}

FLAT_TOOLS = {}
for cat, items in TOOLS.items():
    for name, data in items.items():
        FLAT_TOOLS[name] = data

# --- SESSION STATE ---
if "page" not in st.session_state: st.session_state.page = "home"
if "current_tool" not in st.session_state: st.session_state.current_tool = None
if "chat_histories" not in st.session_state: st.session_state.chat_histories = {t: [] for t in FLAT_TOOLS}
if "api_keys" not in st.session_state: st.session_state.api_keys = {"openai": "", "anthropic": "", "deepseek": ""}

# --- BACKEND LOGIC ---
def get_ai_response(messages, tool_name, model_provider):
    """Robust API Handler with specific error catching"""
    
    # 1. Get System Prompt
    system_prompt = FLAT_TOOLS[tool_name]["prompt"]
    
    # 2. Check Keys
    key_map = {
        "DeepSeek": "deepseek",
        "OpenAI (GPT-4o)": "openai",
        "Claude 3.5 Sonnet": "anthropic"
    }
    
    active_key = st.session_state.api_keys[key_map[model_provider]]
    
    if not active_key:
        return f"⚠️ MISSING API KEY: Please enter your {model_provider} API Key in the sidebar."

    try:
        # --- DEEPSEEK HANDLER ---
        if model_provider == "DeepSeek":
            client = OpenAI(api_key=active_key, base_url="https://api.deepseek.com")
            
            # DeepSeek prefers system prompt in the messages list
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            stream = client.chat.completions.create(
                model="deepseek-chat",
                messages=full_messages,
                stream=True
            )
            return stream

        # --- OPENAI HANDLER ---
        elif model_provider == "OpenAI (GPT-4o)":
            client = OpenAI(api_key=active_key)
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            stream = client.chat.completions.create(
                model="gpt-4o",
                messages=full_messages,
                stream=True
            )
            return stream

        # --- CLAUDE HANDLER ---
        elif model_provider == "Claude 3.5 Sonnet":
            client = Anthropic(api_key=active_key)
            
            with client.messages.stream(
                max_tokens=1024,
                messages=messages, # Claude takes system prompt as a separate arg
                system=system_prompt,
                model="claude-3-5-sonnet-latest",
            ) as stream:
                yield from stream.text_stream

    except Exception as e:
        return f"❌ API ERROR: {str(e)}"

# --- UI COMPONENTS ---

def render_sidebar():
    with st.sidebar:
        st.markdown("### ⚡ NEON OPS")
        
        if st.button("🏠 DASHBOARD", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()

        st.markdown("---")
        st.markdown("### 🔑 API CONFIG")
        
        with st.expander("SET API KEYS", expanded=True):
            st.caption("Keys are stored locally in your session.")
            st.session_state.api_keys["deepseek"] = st.text_input("DeepSeek Key", value=st.session_state.api_keys["deepseek"], type="password", placeholder="sk-...")
            st.session_state.api_keys["anthropic"] = st.text_input("Anthropic Key", value=st.session_state.api_keys["anthropic"], type="password", placeholder="sk-ant-...")
            st.session_state.api_keys["openai"] = st.text_input("OpenAI Key", value=st.session_state.api_keys["openai"], type="password", placeholder="sk-...")

        if st.session_state.page == "chat":
            st.markdown("---")
            st.markdown("### 🎮 CONTROLS")
            
            # Tool Switcher
            new_tool = st.selectbox("ACTIVE TOOL", list(FLAT_TOOLS.keys()), index=list(FLAT_TOOLS.keys()).index(st.session_state.current_tool))
            if new_tool != st.session_state.current_tool:
                st.session_state.current_tool = new_tool
                st.rerun()
                
            # Model Switcher
            model = st.radio("MODEL ENGINE", ["DeepSeek", "Claude 3.5 Sonnet", "OpenAI (GPT-4o)"])
            return model
    return "DeepSeek"

def render_home():
    # Hero Section
    st.markdown(
        """
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="font-size: 3em; margin-bottom: 0;">NEONOPS<span>AI</span></h1>
            <p style="color: #888; font-size: 1.1em; margin-top: 10px;">
                Web3 Command Center | Powered by Multi-Model AI
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Grid Layout
    for category, tools in TOOLS.items():
        st.markdown(f"<h3 style='color: #444 !important; font-size: 1em; margin-top: 30px; border-bottom: 1px solid #222; padding-bottom: 10px;'>{category}</h3>", unsafe_allow_html=True)
        
        cols = st.columns(4)
        tool_list = list(tools.items())
        
        for i, col in enumerate(cols):
            if i < len(tool_list):
                name, data = tool_list[i]
                with col:
                    # Custom formatting for the button content
                    btn_label = f"{data['icon']}  **{name}**\n\n{data['desc']}"
                    if st.button(btn_label, key=f"home_btn_{name}"):
                        st.session_state.current_tool = name
                        st.session_state.page = "chat"
                        st.rerun()

def render_chat(model_provider):
    tool_name = st.session_state.current_tool
    tool_data = FLAT_TOOLS[tool_name]
    
    # Chat Header
    st.markdown(
        f"""
        <div style="border-bottom: 1px solid #222; padding-bottom: 20px; margin-bottom: 20px;">
            <h1 style="margin:0;">{tool_data['icon']} {tool_name}</h1>
            <span style="background: #1a1a1a; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; color: {NEON_GREEN}; border: 1px solid #333;">
                Running on {model_provider}
            </span>
        </div>
        """, 
        unsafe_allow_html=True
    )

    # Chat Area
    for msg in st.session_state.chat_histories[tool_name]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    if prompt := st.chat_input(f"Ask {tool_name}..."):
        # User Msg
        st.session_state.chat_histories[tool_name].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # AI Response
        with st.chat_message("assistant"):
            response_container = st.empty()
            full_res = ""
            
            # Prepare messages
            api_msgs = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_histories[tool_name]]
            
            # Get Stream
            stream = get_ai_response(api_msgs, tool_name, model_provider)
            
            if isinstance(stream, str): # It's an error string
                response_container.error(stream)
                full_res = stream
            else:
                try:
                    for chunk in stream:
                        # Handle logic for different providers
                        content = ""
                        if model_provider == "Claude 3.5 Sonnet":
                            content = chunk
                        else:
                            # OpenAI/DeepSeek
                            if chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                        
                        full_res += content
                        response_container.markdown(full_res + "▌")
                    
                    response_container.markdown(full_res)
                except Exception as e:
                    response_container.error(f"Stream interrupted: {str(e)}")
            
            # Save state
            st.session_state.chat_histories[tool_name].append({"role": "assistant", "content": full_res})

# --- MAIN ---
def main():
    model = render_sidebar()
    
    if st.session_state.page == "home":
        render_home()
    else:
        if st.session_state.current_tool:
            render_chat(model)
        else:
            st.session_state.page = "home"
            st.rerun()

if __name__ == "__main__":
    main()
