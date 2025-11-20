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

# --- CUSTOM CSS (NEON THEME) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Neon Accents */
    h1, h2, h3 {
        color: #00ffcc !important;
        font-family: 'Courier New', monospace;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.3);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Card Styling for Homepage */
    div.stButton > button {
        width: 100%;
        background-color: #21262d;
        color: #c9d1d9;
        border: 1px solid #30363d;
        border-radius: 8px;
        height: 120px;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify_content: center;
    }
    
    div.stButton > button:hover {
        border-color: #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
        transform: translateY(-2px);
        color: #ffffff;
    }
    
    /* Chat Interface Styling */
    .stChatMessage {
        background-color: #21262d;
        border: 1px solid #30363d;
        border-radius: 10px;
    }
    
    /* Utility Classes */
    .category-header {
        color: #7d8590;
        font-size: 0.9em;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-top: 20px;
        margin-bottom: 10px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SYSTEM PROMPTS & TOOL CONFIG ---
TOOLS = {
    "Security": {
        "Token Auditor": {"icon": "🛡️", "prompt": "You are a Web3 Security Auditor. Analyze smart contracts and tokenomics for vulnerabilities, honey-pots, and centralization risks. Be rigorous and paranoid."},
        "Rug Detective": {"icon": "🕵️", "prompt": "You are a Rug Pull Detective. Analyze project roadmaps, team behavior, and liquidity setups for signs of scams. Look for red flags in contract ownership and distribution."},
    },
    "Content": {
        "Viral Engine": {"icon": "🚀", "prompt": "You are a Viral Twitter/X Ghostwriter. Write punchy, engaging, and slightly controversial tweets about crypto. Use hooks, short sentences, and formatting that stops the scroll."},
        "Thread Weaver": {"icon": "🧵", "prompt": "You are a Master Thread Writer. Create educational or narrative Twitter threads. Start with a killer hook, use 10-15 tweets, and end with a CTA."},
        "YT Director": {"icon": "📹", "prompt": "You are a YouTube Scriptwriter for a crypto channel. Create engaging scripts with hooks, intros, detailed body content, and retention hacks."},
    },
    "Growth": {
        "X Scout": {"icon": "🔭", "prompt": "You are a Social Media Analyst. Analyze user profiles, bios, and content strategies to suggest growth hacks and improvements for better engagement."},
        "Airdrop Farmer": {"icon": "🚜", "prompt": "You are an Airdrop Strategy Expert. Provide step-by-step guides to farming potential airdrops. Focus on capital efficiency and transaction volume."},
        "SEO Booster": {"icon": "📈", "prompt": "You are a Web3 SEO Specialist. Optimize content for crypto keywords, suggest meta tags, and improve search rankings for Dapps and blogs."},
    },
    "Development": {
        "Code Breaker": {"icon": "💻", "prompt": "You are a Senior Solidity Developer. Explain complex smart contract code in simple terms. Identify patterns and logic flow."},
        "Data Decoder": {"icon": "🧩", "prompt": "You are a Technical Translator. Take complex whitepapers or technical documentation and simplify it for a 5-year-old (ELI5) or a general investor."},
        "Metadata Forge": {"icon": "🔨", "prompt": "You are an NFT Metadata Specialist. Generate JSON structures for ERC-721/1155 tokens. Ensure OpenSea compatibility."},
    },
    "Mental": {
        "Psych Coach": {"icon": "🧠", "prompt": "You are a Trading Psychology Coach. Help the user manage FOMO, revenge trading, and emotional decision making. Be stoic and logical."},
    }
}

FLAT_TOOLS_LIST = []
for cat, tools in TOOLS.items():
    for name, data in tools.items():
        FLAT_TOOLS_LIST.append(name)

# --- SESSION STATE INITIALIZATION ---
if "page" not in st.session_state:
    st.session_state.page = "home"
if "current_tool" not in st.session_state:
    st.session_state.current_tool = None
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {tool: [] for tool in FLAT_TOOLS_LIST}
if "api_keys" not in st.session_state:
    st.session_state.api_keys = {"openai": "", "anthropic": "", "deepseek": ""}

# --- BACKEND LOGIC ---
def get_ai_response(messages, tool_name, model_provider):
    """
    Handles API calls to DeepSeek, OpenAI, or Claude.
    """
    system_prompt = ""
    for cat in TOOLS.values():
        if tool_name in cat:
            system_prompt = cat[tool_name]["prompt"]
            break

    # Prepend system prompt
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        if model_provider == "DeepSeek":
            api_key = st.session_state.api_keys["deepseek"]
            if not api_key:
                return "⚠️ Please enter your DeepSeek API Key in the sidebar."
            
            # DeepSeek is OpenAI Compatible
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=full_messages,
                stream=True
            )
            return response

        elif model_provider == "OpenAI (GPT-4o)":
            api_key = st.session_state.api_keys["openai"]
            if not api_key:
                return "⚠️ Please enter your OpenAI API Key in the sidebar."
            
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=full_messages,
                stream=True
            )
            return response

        elif model_provider == "Claude 3.5 Sonnet":
            api_key = st.session_state.api_keys["anthropic"]
            if not api_key:
                return "⚠️ Please enter your Anthropic API Key in the sidebar."
            
            client = Anthropic(api_key=api_key)
            # Claude handles system prompts separately
            system_msg = full_messages.pop(0)["content"]
            
            with client.messages.stream(
                max_tokens=1024,
                messages=messages, # Pass user messages only
                system=system_msg,
                model="claude-3-5-sonnet-latest",
            ) as stream:
                yield from stream.text_stream

    except Exception as e:
        return f"❌ API Error: {str(e)}"

# --- UI COMPONENTS ---

def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚡ Control Panel")
        
        # Navigation
        if st.button("🏠 Home Dashboard", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        
        st.markdown("---")
        
        # API Key Management
        st.markdown("### 🔑 API Keys")
        with st.expander("Manage Keys", expanded=False):
            st.session_state.api_keys["deepseek"] = st.text_input("DeepSeek Key", value=st.session_state.api_keys["deepseek"], type="password")
            st.session_state.api_keys["anthropic"] = st.text_input("Anthropic Key", value=st.session_state.api_keys["anthropic"], type="password")
            st.session_state.api_keys["openai"] = st.text_input("OpenAI Key", value=st.session_state.api_keys["openai"], type="password")
            
        st.markdown("---")
        
        # Tool Selector (Only visible in Chat)
        if st.session_state.page == "chat":
            st.markdown("### 🛠️ Active Tool")
            selected_tool = st.selectbox(
                "Switch Tool",
                FLAT_TOOLS_LIST,
                index=FLAT_TOOLS_LIST.index(st.session_state.current_tool) if st.session_state.current_tool else 0
            )
            
            # Update tool if changed via selectbox
            if selected_tool != st.session_state.current_tool:
                st.session_state.current_tool = selected_tool
                st.rerun()

            st.markdown("### 🧠 AI Model")
            model_choice = st.radio(
                "Select Engine:",
                ["DeepSeek", "Claude 3.5 Sonnet", "OpenAI (GPT-4o)"],
                index=0
            )
            return model_choice
    return None

def render_home():
    st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>NeonOps AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888; margin-bottom: 40px;'>Web3 Command Center | Powered by DeepSeek, Claude & OpenAI</p>", unsafe_allow_html=True)

    # Render Categories
    for category, tools in TOOLS.items():
        st.markdown(f"<div class='category-header'>{category}</div>", unsafe_allow_html=True)
        
        # Create a grid for this category
        cols = st.columns(4) # 4 cards per row
        tool_names = list(tools.keys())
        
        for i, col in enumerate(cols):
            if i < len(tool_names):
                tool_name = tool_names[i]
                tool_data = tools[tool_name]
                
                with col:
                    # We use a button as a card
                    if st.button(f"{tool_data['icon']}\n\n{tool_name}", key=f"btn_{tool_name}"):
                        st.session_state.current_tool = tool_name
                        st.session_state.page = "chat"
                        st.rerun()

def render_chat(model_provider):
    tool_name = st.session_state.current_tool
    
    # Header
    col1, col2 = st.columns([1, 8])
    with col1:
        st.markdown(f"<h1>{st.session_state.current_tool}</h1>", unsafe_allow_html=True)
    with col2:
        # Find icon
        icon = ""
        for cat in TOOLS.values():
            if tool_name in cat:
                icon = cat[tool_name]['icon']
        st.markdown(f"### {icon} - {model_provider}")

    # Chat History Container
    chat_container = st.container()
    
    # Input Area
    prompt = st.chat_input(f"Ask {tool_name}...")

    # Display History
    with chat_container:
        for message in st.session_state.chat_histories[tool_name]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Handle New Message
    if prompt:
        # 1. Display User Message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 2. Add to history
        st.session_state.chat_histories[tool_name].append({"role": "user", "content": prompt})
        
        # 3. Generate Response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            # Convert history to API format
            api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_histories[tool_name]]
            
            # Call API Wrapper
            stream_generator = get_ai_response(api_messages, tool_name, model_provider)
            
            if isinstance(stream_generator, str):
                # Error message
                response_placeholder.error(stream_generator)
                full_response = stream_generator
            else:
                # Stream response
                try:
                    for chunk in stream_generator:
                        # Handle OpenAI/DeepSeek vs Claude chunk differences
                        content = ""
                        if model_provider == "Claude 3.5 Sonnet":
                            content = chunk # Anthropic returns text directly in the yield above
                        else:
                            # OpenAI/DeepSeek
                            if chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                        
                        full_response += content
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                except Exception as e:
                    response_placeholder.error(f"Stream Error: {e}")
                    full_response = str(e)

        # 4. Save Assistant Response
        st.session_state.chat_histories[tool_name].append({"role": "assistant", "content": full_response})

# --- MAIN APP FLOW ---
def main():
    model_choice = render_sidebar()
    
    if st.session_state.page == "home":
        render_home()
    elif st.session_state.page == "chat":
        if not st.session_state.current_tool:
            st.session_state.page = "home"
            st.rerun()
        render_chat(model_choice)

if __name__ == "__main__":
    main()
