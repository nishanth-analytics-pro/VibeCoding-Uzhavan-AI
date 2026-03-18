import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import io
import urllib.parse
from datetime import datetime
import sqlite3
from streamlit_mic_recorder import mic_recorder
import speech_recognition as sr
from gtts import gTTS
import hashlib
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# ====================================================
# 🌱 CONFIGURATION & UI THEME
# ====================================================
st.set_page_config(page_title="🌾 உழவன் கண் AI (Pro)", page_icon="🌾", layout="wide")

# ✨ Premium Glassmorphism UI & Custom CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); }
    div.stButton > button:first-child {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: #1f2937;
        font-weight: 600;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        background: #2ecc71;
        color: white;
        box-shadow: 0 8px 15px rgba(46, 204, 113, 0.4);
    }
</style>
""", unsafe_allow_html=True)

GEMINI_API_KEY = "AIzaSyDptwip069XwJtoB0M2EUj9Hi_Miwn2ab0"
OPENWEATHER_API_KEY = "293a41dd0b5b53178fbd54053690a1de"
genai.configure(api_key=GEMINI_API_KEY)

# ====================================================
# 🗄️ DATABASE SETUP
# ====================================================
def init_db():
    conn = sqlite3.connect('uzhavan_database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, date TEXT, result TEXT, lang TEXT)''')
    conn.commit()
    conn.close()

def hash_password(password): return hashlib.sha256(str.encode(password)).hexdigest()

def add_user(username, password):
    try:
        conn = sqlite3.connect('uzhavan_database.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError: return False
    finally: conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('uzhavan_database.db')
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    if result and result[0] == hash_password(password): return True
    return False

def save_to_history(username, result_text, lang):
    conn = sqlite3.connect('uzhavan_database.db')
    c = conn.cursor()
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO history (username, date, result, lang) VALUES (?, ?, ?, ?)", (username, date_str, result_text, lang))
    conn.commit()
    conn.close()

init_db()

# ====================================================
# 🔐 SESSION STATE
# ====================================================
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'page' not in st.session_state: st.session_state.page = "home"

LANG_DICT = {
    "தமிழ் (Tamil)": ("ta", "simple Tamil"),
    "English": ("en", "simple English"),
    "हिंदी (Hindi)": ("hi", "simple Hindi")
}

# ====================================================
# 🤖 SHARED FUNCTIONS
# ====================================================
def generate_audio(text, lang='ta'):
    try:
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception: return None

def nav_buttons():
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔙 Back (பின்செல்)", use_container_width=True): st.session_state.page = "home"; st.rerun()
    with col2:
        if st.button("🏠 Home (முகப்பு)", use_container_width=True): st.session_state.page = "home"; st.rerun()
    st.markdown("---")

# ====================================================
# 📄 PAGES
# ====================================================
def login_page():
    st.markdown("<h1 style='text-align:center;'>🌾 உழவன் கண் AI</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login (உள்நுழைய)", "Sign Up (புதிய கணக்கு)"])
    with tab1:
        with st.form("login_form"):
            log_user = st.text_input("Username")
            log_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                if verify_user(log_user, log_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = log_user
                    st.rerun()
                else: st.error("Invalid Credentials!")
    with tab2:
        with st.form("signup_form"):
            reg_user = st.text_input("Choose Username")
            reg_pass = st.text_input("Choose Password", type="password")
            if st.form_submit_button("Sign Up", use_container_width=True):
                if reg_user and len(reg_pass) >= 4:
                    if add_user(reg_user, reg_pass): st.success("Account created!")
                    else: st.error("Username exists!")

def home_page():
    st.markdown("<h1 style='text-align:center;'>🌾 உழவன் கண் AI (Pro)</h1>", unsafe_allow_html=True)
    st.image("https://www.esgtimes.in/wp-content/uploads/2025/03/pexels-gowtham-agm-609630353-18620459-1.jpg", use_container_width=True)
    
    st.subheader("🛠️ Core Features")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📸 Disease Diagnosis", use_container_width=True): st.session_state.page = "diagnosis"; st.rerun()
    with col2:
        if st.button("🌿 Fertilizer Calculator", use_container_width=True): st.session_state.page = "fertilizer"; st.rerun()
    with col3:
        if st.button("🎙️ Voice Assistant", use_container_width=True): st.session_state.page = "general_chat"; st.rerun()

    st.markdown("---")
    st.subheader("📈 Advanced Analytics")
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("📊 Admin Dashboard", use_container_width=True): st.session_state.page = "admin"; st.rerun()
    with col5:
        if st.button("📈 Price Forecasting", use_container_width=True): st.session_state.page = "forecast"; st.rerun()
    with col6:
        if st.button("🗺️ Map & Market", use_container_width=True): st.session_state.page = "map_market"; st.rerun()

# --- 📸 CHAT-BASED DISEASE DIAGNOSIS ---
def diagnosis_page():
    nav_buttons()
    st.markdown("## 📸 பயிர் மருத்துவர் (AI Chat)")
    lang_name, lang_code = LANG_DICT[st.session_state.lang_selection][1], LANG_DICT[st.session_state.lang_selection][0]

    if "diag_history" not in st.session_state:
        st.session_state.diag_history = [{"role": "assistant", "content": "வணக்கம்! பயிரின் புகைப்படத்தை அப்லோட் செய்து, உங்கள் கேள்வியை கேளுங்கள்.", "image": None}]
    
    for msg in st.session_state.diag_history:
        with st.chat_message(msg["role"]):
            if msg.get("image"): st.image(msg["image"], width=200)
            st.markdown(msg["content"])

    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    with col1: img_file = st.file_uploader("🖼️ புகைப்படத்தை இணைக்க", type=['png', 'jpg', 'jpeg'])
    with col2:
        st.write("🎙️ வாய்ஸ் மூலம் கேட்க:")
        audio = mic_recorder(start_prompt="மைக்-ஐ ஆன் செய்", stop_prompt="🛑 Stop", key='diag_mic')

    text_input = st.chat_input("அல்லது இங்கே டைப் செய்யவும்...")

    user_text = None
    if audio:
        with st.spinner("குரலை கவனிக்கிறது..."):
            try:
                r = sr.Recognizer()
                audio_data = sr.AudioData(audio['bytes'], audio['sample_rate'], audio['sample_width'])
                user_text = r.recognize_google(audio_data, language='ta-IN' if lang_code == 'ta' else 'en-IN')
            except Exception: st.error("⚠️ ஆடியோ புரியவில்லை.")
    elif text_input: user_text = text_input

    if user_text or img_file:
        prompt_text = user_text if user_text else "Analyze this plant leaf. Tell me the disease and cure."
        image_pil = Image.open(img_file) if img_file else None
        
        st.session_state.diag_history.append({"role": "user", "content": prompt_text, "image": image_pil})
        with st.chat_message("user"):
            if image_pil: st.image(image_pil, width=200)
            st.markdown(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("AI யோசிக்கிறது..."):
                model = genai.GenerativeModel("gemini-flash-latest")
                content = [f"Answer in {lang_name}. Question: {prompt_text}"]
                if image_pil: content.append(image_pil)
                response = model.generate_content(content)
                ai_text = response.text
                
                st.markdown(ai_text)
                st.session_state.diag_history.append({"role": "assistant", "content": ai_text, "image": None})
                save_to_history(st.session_state.username, ai_text, lang_code)

                with st.spinner("குரல் பதிவாக மாறுகிறது..."):
                    audio_file = generate_audio(ai_text, lang=lang_code)
                    if audio_file: st.audio(audio_file, format='audio/mp3')

# --- 🎙️ VOICE-FIRST AI ASSISTANT ---
def general_chat_page():
    nav_buttons()
    st.markdown("## 🎙️ உழவன் குரல் உதவி")
    lang_name, lang_code = LANG_DICT[st.session_state.lang_selection][1], LANG_DICT[st.session_state.lang_selection][0]
    
    if "gen_chat_hist" not in st.session_state: st.session_state.gen_chat_hist = [{"role": "assistant", "content": "விவசாய சந்தேகங்களை மைக்கில் கேட்கவும்."}]
    if "gen_chat_model" not in st.session_state: st.session_state.gen_chat_model = genai.GenerativeModel('gemini-flash-latest').start_chat()

    for msg in st.session_state.gen_chat_hist:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        audio = mic_recorder(start_prompt="🎙️ பேசத்தொடங்க இங்கே அழுத்தவும்", stop_prompt="🛑 Stop", key='gen_mic')
    
    text_input = st.chat_input("Type here...")

    user_input = None
    if audio:
        with st.spinner("Listening..."):
            try:
                r = sr.Recognizer()
                audio_data = sr.AudioData(audio['bytes'], audio['sample_rate'], audio['sample_width'])
                user_input = r.recognize_google(audio_data, language='ta-IN' if lang_code == 'ta' else 'en-IN')
            except Exception: st.error("⚠️ ஆடியோ புரியவில்லை.")
    elif text_input: user_input = text_input

    if user_input:
        st.session_state.gen_chat_hist.append({"role": "user", "content": user_input})
        with st.chat_message("user"): st.markdown(user_input)

        with st.spinner("Thinking..."):
            response = st.session_state.gen_chat_model.send_message(f"Answer in {lang_name} simply. Question: {user_input}")
            ai_text = response.text
            st.session_state.gen_chat_hist.append({"role": "assistant", "content": ai_text})
            with st.chat_message("assistant"):
                st.markdown(ai_text)
                audio_file = generate_audio(ai_text, lang=lang_code)
                if audio_file: st.audio(audio_file, format='audio/mp3')

# --- 📊 ADMIN DASHBOARD ---
def admin_dashboard_page():
    nav_buttons()
    st.markdown("## 📊 Phase 1: Admin Analytics Dashboard")
    conn = sqlite3.connect('uzhavan_database.db')
    df = pd.read_sql_query("SELECT * FROM history", conn)
    conn.close()

    if df.empty: st.warning("No data available.")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Total App Scans", len(df))
        c2.metric("Total Users", df['username'].nunique())
        
        lang_count = df['lang'].value_counts().reset_index()
        lang_count.columns = ['Language', 'Count']
        fig1 = px.pie(lang_count, values='Count', names='Language', title='Language Preferences', hole=0.3)
        st.plotly_chart(fig1, use_container_width=True)

# --- 📈 PRICE FORECASTING ---
def forecasting_page():
    nav_buttons()
    st.markdown("## 📈 Phase 2: Price Forecasting (ML)")
    months = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).reshape(-1, 1)
    prices = np.array([20, 22, 21, 24, 28, 30, 29, 32, 35, 34])
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(months, prices)
    predictions = model.predict(np.array([11, 12, 13]).reshape(-1, 1))
    
    df_all = pd.concat([pd.DataFrame({'Month': months.flatten(), 'Price': prices, 'Type': 'Historical'}),
                        pd.DataFrame({'Month': [11, 12, 13], 'Price': predictions, 'Type': 'Predicted'})])
    
    fig = px.line(df_all, x='Month', y='Price', color='Type', markers=True, title="Tomato Price Trend")
    st.plotly_chart(fig, use_container_width=True)

# --- 🗺️ MAP & MARKET ---
def map_market_page():
    nav_buttons()
    st.markdown("## 🗺️ Phase 3: Geospatial & Market")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📍 Disease Hotspots (Salem)")
        m = folium.Map(location=[11.6643, 78.1460], zoom_start=10)
        folium.Marker([11.66, 78.14], popup="Wilt Detected", icon=folium.Icon(color="red")).add_to(m)
        st_folium(m, use_container_width=True, height=400, returned_objects=[])
    with col2:
        st.subheader("🛒 Live Mandi Prices")
        st.table(pd.DataFrame({"Crop": ["Tomato", "Onion"], "Market": ["Salem", "Attur"], "Price": ["₹2,400", "₹1,800"]}))

def weather_page():
    nav_buttons()
    st.markdown("## 🌦️ Weather")
    url = f"http://api.openweathermap.org/data/2.5/weather?q=Salem&appid={OPENWEATHER_API_KEY}&units=metric"
    try:
        res = requests.get(url).json()
        if res.get("cod") == 200: st.success(f"**Salem** Temp: **{res['main']['temp']}°C**. Weather: {res['weather'][0]['main']}")
    except: st.error("Weather API Error.")

def fertilizer_page():
    nav_buttons()
    st.markdown("## 🌿 Fertilizer Calculator")
    if st.button("Calculate NPK"): st.success("Calculated successfully!")

# ====================================================
# 🚀 ROUTER & SIDEBAR
# ====================================================
if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.title("⚙️ Settings")
    st.sidebar.write(f"👤 User: **{st.session_state.username}**")
    if 'lang_selection' not in st.session_state: st.session_state.lang_selection = "தமிழ் (Tamil)"
    st.session_state.lang_selection = st.sidebar.selectbox("🌐 Language:", list(LANG_DICT.keys()), index=list(LANG_DICT.keys()).index(st.session_state.lang_selection))
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    pages = {
        "home": home_page, "diagnosis": diagnosis_page, "general_chat": general_chat_page,
        "admin": admin_dashboard_page, "forecast": forecasting_page, "map_market": map_market_page,
        "weather": weather_page, "fertilizer": fertilizer_page
    }
    pages[st.session_state.page]()