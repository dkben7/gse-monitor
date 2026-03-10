import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('gse_final.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS portfolio 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, ticker TEXT, shares REAL, change REAL)''')
    conn.commit()
    conn.close()

# --- MOBILE STYLING ---
st.set_page_config(page_title="GSE Mobile", layout="wide")
init_db()

st.markdown("""
    <style>
    /* Mobile-First Adjustments */
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007AFF; color: white; }
    [data-testid="stMetric"] { background: #1e1e1e; border: 1px solid #333; border-radius: 15px; }
    .ticker-card { padding: 10px; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }
    </style>
    """, unsafe_allow_html=True)

# --- APP LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Centered Mobile Login
    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.title("🏦 GSE Intelligence")
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            u = st.text_input("Username").lower()
            p = st.text_input("Password", type="password")
            if st.button("Sign In"):
                st.session_state.logged_in = True # Simplified for demo
                st.session_state.user = u
                st.rerun()
else:
    # --- DASHBOARD ---
    st.header(f"Welcome, {st.session_state.user.capitalize()}")
    
    # Add Section
    with st.expander("➕ Add New Stock"):
        t = st.text_input("Ticker").upper()
        s = st.number_input("Shares", step=1.0)
        c = st.number_input("Change")
        if st.button("Add to Portfolio"):
            conn = sqlite3.connect('gse_final.db')
            conn.execute("INSERT INTO portfolio (username, ticker, shares, change) VALUES (?,?,?,?)", 
                         (st.session_state.user, t, s, c))
            conn.commit()
            st.rerun()

    # Display Data with Delete Option
    conn = sqlite3.connect('gse_final.db')
    df = pd.read_sql(f"SELECT * FROM portfolio WHERE username='{st.session_state.user}'", conn)
    
    if not df.empty:
        st.subheader("Your Holdings")
        for i, row in df.iterrows():
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{row['ticker']}** ({row['shares']} shares)")
            color = "green" if row['change'] > 0 else "red"
            c2.write(f":{color}[{row['change']}%]")
            if c3.button("🗑️", key=f"del_{row['id']}"):
                conn.execute(f"DELETE FROM portfolio WHERE id={row['id']}")
                conn.commit()
                st.rerun()
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.rerun()
