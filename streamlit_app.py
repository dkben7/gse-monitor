import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('gse_pro_v2.db')
    c = conn.cursor()
    # User Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Transactions Table (User-Specific)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  ticker TEXT, 
                  shares REAL, 
                  buy_price REAL, 
                  daily_change REAL)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_login(username, password):
    conn = sqlite3.connect('gse_pro_v2.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password =?', (username, make_hashes(password)))
    data = c.fetchone()
    conn.close()
    return data

# --- 2. THEME & UI ---
st.set_page_config(page_title="GSE Intelligence Pro", page_icon="🏦", layout="wide")
init_db()

# Custom CSS for Centering and Theme
st.markdown("""
    <style>
    .centered-box { max-width: 500px; margin: 0 auto; padding-top: 100px; }
    [data-testid="stMetric"] { background-color: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.1); }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. THE GATEWAY (LOGIN/SIGNUP) ---
if not st.session_state.logged_in:
    # Creating a centered layout
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        st.title("🏦 GSE Pro Monitor")
        choice = st.tabs(["Login", "Sign Up"])
        
        with choice[0]:
            user = st.text_input("Username").lower()
            pwd = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True):
                if check_login(user, pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        
        with choice[1]:
            new_user = st.text_input("New Username").lower()
            new_pwd = st.text_input("New Password", type="password")
            if st.button("Create Account", use_container_width=True):
                try:
                    conn = sqlite3.connect('gse_pro_v2.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_user, make_hashes(new_pwd)))
                    conn.commit()
                    st.success("Registration successful! Switch to Login.")
                except:
                    st.error("Username already exists.")

# --- 4. THE MONITORING APP (POST-LOGIN) ---
else:
    # Professional Sidebar
    with st.sidebar:
        st.header(f"👤 {st.session_state.username.title()}")
        st.divider()
        # Simple Light/Dark Logic (Streamlit handles actual theme, this is for UI toggles)
        mode = st.toggle("Dark Mode Optimized", value=True)
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun
