import streamlit as st
import anthropic
from duckduckgo_search import DDGS
import time
import random

# --- 1. PAGE CONFIG (IMMERSIVE) ---
st.set_page_config(
    page_title="AnimeOps AI",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. ANIME RPG CSS (3D & ANIMATIONS) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Roboto:wght@400;700&display=swap');

    /* GLOBAL RESET */
    .stApp {
        background-color: #0a0a0a;
        background-image: url("https://www.transparenttextures.com/patterns/cubes.png");
        color: white;
    }

    /* 3D CARD EFFECT */
    .anime-card {
        background: linear-gradient(145deg, #1a1a1a, #222);
        border: 2px solid #333;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        transition: transform 0.3s, box-shadow 0.3s;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    .anime-card:hover {
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 20px 40px rgba(0, 255, 255, 0.2);
        border-color: #00f0ff;
    }
    
    /* CHARACTER THEMES */
    .theme-saiyan { border-color: #ff9900; box-shadow: 0 0 10px rgba(255, 153, 0, 0.3); }
    .theme-saiyan:hover { box-shadow: 0 0 30px #ff9900; }
    
    .theme-ninja { border-color: #ff0055; box-shadow: 0 0 10px rgba(255, 0, 85, 0.3); }
    .theme-ninja:hover { box-shadow: 0 0 30px #ff0055; }

    .theme-sorcerer { border-color: #a000ff; box-shadow: 0 0 10px rgba(160, 0, 255, 0.3); }
    .theme-sorcerer:hover { box-shadow: 0 0 30px #a000ff; }

    /* HEADERS */
    h1, h2, h3 { font-family: 'Bangers', cursive; letter-spacing: 2px; }
    h1 { font-size: 60px !important; text-shadow: 3px 3px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000; }
    
    /* CHAT BUBBLES */
    .stChatMessage {
        background: rgba(0,0,0,0.6);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 10px;
        backdrop-filter: blur(5px);
    }
    
    /* ULTIMATE BAR */
    .ult-bar-bg { width: 100%; height: 10px; background: #333; border-radius: 5px; margin-top: 10px; }
    .ult-bar-fill { height: 100%; background: linear-gradient(90deg, #ff0000, #ffff00); border-radius: 5px; transition: width 1s; }

</style>
""", unsafe_allow_html=True)

# --- 3. STATE MANAGEMENT ---
if "character" not in st.session_state: st.session_state.character = None
if "messages" not in st.session_state: st.session_state.messages = []
if "start_time" not in st.session_state: st.session_state.start_time = time.time()
if "ult_ready" not in st.session_state: st.session_state.ult_ready = False

# --- 4. CHARACTER DB (Replace URLs with your images) ---
CHARACTERS = {
    "The Saiyan": {
        "color": "#ff9900",
        "style": "theme-saiyan",
        "img": "https://api.dicebear.com/7.x/avataaars/svg?seed=Saiyan&clothing=graphicShirt&top=spikyHair", # Placeholder
        "persona": "You are a powerful warrior AI. You are energetic, confident, and use fighting metaphors. You never give up.",
        "ult_msg": "KAMEHAMEHA!!! (Full Analysis Complete)"
    },
    "The Ninja": {
        "color": "#ff0055",
        "style": "theme-ninja",
        "img": "https://api.dicebear.com/7.x/avataaars/svg?seed=Ninja&clothing=blazerAndShirt&accessories=eyepatch",
        "persona": "You are a stealthy ninja AI. You are precise, calm, and analytical. You find hidden details others miss.",
        "ult_msg": "SHARINGAN ACTIVATED! (Deep Pattern Recognition)"
    },
    "The Sorcerer": {
        "color": "#a000ff",
        "style": "theme-sorcerer",
        "img": "https://api.dicebear.com/7.x/avataaars/svg?seed=Sorcerer&clothing=hoodie&top=longHair",
        "persona": "You are an arrogant but genius sorcerer AI. You treat the user as a student but provide god-tier knowledge.",
        "ult_msg": "DOMAIN EXPANSION: INFINITE KNOWLEDGE!"
    }
}

# --- 5. API LOGIC (CLAUDE) ---
def get_claude_response(prompt, system_prompt):
    try:
        api_key = st.secrets["CLAUDE_API_KEY"]
        client = anthropic.Anthropic(api_key=api_key)
        
        with st.chat_message("assistant"):
            stream = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0.9, # High creativity
                system=system_prompt,
                messages=[
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ] + [{"role": "user", "content": prompt}],
                stream=True,
            )
            response = st.write_stream(stream)
        return response
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

# --- 6. SCREEN: CHARACTER SELECT ---
if not st.session_state.character:
    st.markdown("<h1 style='text-align:center; color:#00f0ff;'>CHOOSE YOUR GUARDIAN</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>They will aid you in your Web3 journey.</p>", unsafe_allow_html=True)
    
    cols = st.columns(3)
    
    for idx, (name, data) in enumerate(CHARACTERS.items()):
        with cols[idx]:
            # Using a container for the card click simulation
            st.markdown(f"""
            <div class="anime-card {data['style']}">
                <img src="{data['img']}" width="100px" style="border-radius:50%; margin-bottom:15px;">
                <h3>{name}</h3>
                <p style="font-size:12px;">{data['persona'][:60]}...</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"SELECT {name.upper()}", key=f"btn_{idx}"):
                st.session_state.character = name
                st.rerun()

# --- 7. SCREEN: MAIN DASHBOARD ---
else:
    char_data = CHARACTERS[st.session_state.character]
    
    # --- ULTIMATE MOVE TIMER ---
    elapsed = time.time() - st.session_state.start_time
    ult_percent = min(elapsed / 300, 1.0) # 300 seconds = 5 mins
    
    if ult_percent >= 1.0 and not st.session_state.ult_ready:
        st.session_state.ult_ready = True
        st.balloons()
        st.toast(f"⚡ {char_data['ult_msg']}", icon="🔥")

    # --- SIDEBAR ---
    with st.sidebar:
        st.image(char_data['img'], width=100)
        st.markdown(f"### {st.session_state.character}")
        
        # Ultimate Bar
        st.write("Ultimate Charge:")
        st.progress(ult_percent)
        if st.session_state.ult_ready:
            if st.button("☄️ UNLEASH ULTIMATE"):
                st.snow()
                st.session_state.start_time = time.time() # Reset
                st.session_state.ult_ready = False
                st.rerun()

        st.markdown("---")
        st.write("**Select Ability:**")
        tool = st.radio("", ["Viral Tweet Gen", "Smart Contract Audit", "Market Intel", "Meme Idea", "Unrestricted Chat"])
        
        if st.button("⬅️ Change Character"):
            st.session_state.character = None
            st.rerun()

    # --- MAIN CHAT ---
    st.title(f"{tool}")
    
    # Render Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User Input
    if prompt := st.chat_input("Enter your command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        # Context Building
        context = f"You are playing the character: {st.session_state.character}. {char_data['persona']}. The user wants to use the tool: {tool}."
        
        # Run AI
        response = get_claude_response(prompt, context)
        
        if response:
            st.session_state.messages.append({"role": "assistant", "content": response})
            # Keep chat history manageable (last 10 messages)
            if len(st.session_state.messages) > 10:
                st.session_state.messages = st.session_state.messages[-10:]
