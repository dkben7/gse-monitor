import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# --- 1. DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect('gse_pro.db')
    c = conn.cursor()
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, theme TEXT DEFAULT 'Dark')''')
    # Transactions Table (The core data)
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT, 
                  ticker TEXT, 
                  shares REAL, 
                  buy_price REAL, 
                  change REAL)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def login_user(username, password):
    conn = sqlite3.connect('gse_pro.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username =? AND password =?', (username, make_hashes(password)))
    data = c.fetchone()
    conn.close()
    return data

# --- 2. THEME & UI STYLE ---
st.set_page_config(page_title="GSE Pro", layout="wide")
init_db()

# Centered Login Style
st.markdown("""
    <style>
    .stApp { max-width: 1000px; margin: 0 auto; }
    [data-testid="stMetric"] { background-color: rgba(255, 255, 255, 0.05); border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Session State Initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. LOGIN / SIGNUP PAGE (CENTERED) ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏦 GSE Intelligence Pro")
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            user = st.text_input("Username").lower()
            pwd = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True):
                result = login_user(user, pwd)
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        
        with tab2:
            new_user = st.text_input("Choose Username").lower()
            new_pwd = st.text_input("Choose Password", type="password")
            if st.button("Register Account", use_container_width=True):
                try:
                    conn = sqlite3.connect('gse_pro.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO users(username, password) VALUES (?,?)', (new_user, make_hashes(new_pwd)))
                    conn.commit()
                    st.success("Account created! You can now login.")
                except:
                    st.error("Username already taken.")

# --- 4. THE MAIN APP (POST-LOGIN) ---
else:
    # Sidebar for Logout and Settings
    with st.sidebar:
        st.header(f"👋 {st.session_state.username.title()}")
        # Theme Toggle (Note: Streamlit has a built-in toggle in Settings, 
        # but we can simulate a light/dark UI switch here)
        theme = st.toggle("Enable Light Mode UI")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📈 Market Dashboard")
    
    # 5. DATA MANAGEMENT SECTION
    with st.expander("➕ Add New Transaction"):
        c1, c2, c3, c4 = st.columns(4)
        t_ticker = c1.text_input("Ticker (e.g. MTN)").upper()
        t_shares = c2.number_input("Shares", min_value=0.0)
        t_price = c3.number_input("Buy Price", min_value=0.0)
        t_change = c4.number_input("Daily Change", format="%.2f")
        
        if st.button("Save Transaction"):
            conn = sqlite3.connect('gse_pro.db')
            c = conn.cursor()
            c.execute('INSERT INTO transactions(username, ticker, shares, buy_price, change) VALUES (?,?,?,?,?)',
                      (st.session_state.username, t_ticker, t_shares, t_price, t_change))
            conn.commit()
            st.success(f"Added {t_ticker} to your portfolio!")
            st.rerun()

    # 6. DASHBOARD LOGIC
    conn = sqlite3.connect('gse_pro.db')
    df = pd.read_sql(f"SELECT * FROM transactions WHERE username='{st.session_state.username}'", conn)
    conn.close()

    if not df.empty:
        # Filter Ghost Zeros
        df = df[df['change'] != 0]
        
        # Metrics
        m1, m2 = st.columns(2)
        m1.metric("Total Holdings", f"{len(df)} Stocks")
        m2.metric("Portfolio Status", "Active", delta="Live")

        # Tables
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("🚀 Top Performers")
            st.dataframe(df[df['change'] > 0].nlargest(5, 'change')[['ticker', 'change']], hide_index=True)
        with col_right:
            st.subheader("📉 Top Losers")
            st.dataframe(df[df['change'] < 0].nsmallest(5, 'change')[['ticker', 'change']], hide_index=True)
    else:
        st.info("Your portfolio is empty. Add a transaction above to see your data!")
