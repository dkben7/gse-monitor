import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# --- 1. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Added 'sheet_id' column to the user table
    c.execute('''CREATE TABLE IF NOT EXISTS userstable
                 (username TEXT PRIMARY KEY, password TEXT, sheet_id TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text:
        return hashed_text
    return False

def create_user(username, password, sheet_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO userstable(username, password, sheet_id) VALUES (?,?,?)', 
                  (username, make_hashes(password), sheet_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM userstable WHERE username =?', (username,))
    data = c.fetchone()
    conn.close()
    if data and check_hashes(password, data[1]):
        return data
    return None

# --- 2. DATA ENGINE ---
def get_gse_data(sheet_id):
    base_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    
    # Load Portfolio
    p_df = pd.read_csv(f"{base_url}&sheet=Portfolio")
    
    # GLOBAL CAPITALIZATION (Columns & First Word)
    p_df.columns = [col.strip().title() for col in p_df.columns]
    p_df.iloc[:, 0] = p_df.iloc[:, 0].astype(str).str.title()
    
    # CLEANING & GHOST ZERO REMOVAL
    # Logic: Convert brackets to negatives and filter out 0 values
    p_df['Clean_Change'] = p_df.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    p_df['Clean_Change'] = pd.to_numeric(p_df['Clean_Change'], errors='coerce').fillna(0)
    
    # Robust Filter: Remove rows where Change is 0 OR Ticker is empty
    p_df = p_df[(p_df['Clean_Change'] != 0) & (p_df.iloc[:, 0].str.strip() != "")]
    
    return p_df

# --- 3. UI LAYOUT ---
st.set_page_config(page_title="GSE Pro Monitor", layout="wide")
init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Sidebar for Login/Signup
with st.sidebar:
    st.title("🏦 GSE Access")
    if not st.session_state.logged_in:
        auth_mode = st.radio("Choose Action", ["Login", "Create Account"])
        
        if auth_mode == "Create Account":
            new_user = st.text_input("New Username").lower()
            new_pass = st.text_input("New Password", type="password")
            new_sid = st.text_input("Your Google Sheet ID")
            if st.button("Register"):
                if create_user(new_user, new_pass, new_sid):
                    st.success("Account Created! Switch to Login.")
                else:
                    st.error("Username already exists.")
                    
        else:
            user = st.text_input("Username").lower()
            pwd = st.text_input("Password", type="password")
            if st.button("Login"):
                userdata = login_user(user, pwd)
                if userdata:
                    st.session_state.logged_in = True
                    st.session_state.username = userdata[0]
                    st.session_state.sheet_id = userdata[2]
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    else:
        st.success(f"Welcome, {st.session_state.username.title()}!")
        if st.button("Sign Out"):
            st.session_state.logged_in = False
            st.rerun()

# --- 4. MAIN DASHBOARD ---
if st.session_state.logged_in:
    st.title(f"📊 {st.session_state.username.title()}'s Real-Time Monitor")
    
    try:
        df = get_gse_data(st.session_state.sheet_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚀 Top Performers")
            gainers = df[df['Clean_Change'] > 0].nlargest(5, 'Clean_Change')
            st.dataframe(gainers.iloc[:, [0, -1]], hide_index=True, use_container_width=True)
            
        with col2:
            st.subheader("📉 Top Losers")
            losers = df[df['Clean_Change'] < 0].nsmallest(5, 'Clean_Change')
            st.dataframe(losers.iloc[:, [0, -1]], hide_index=True, use_container_width=True)

    except Exception as e:
        st.error("Could not load your specific Google Sheet. Check your ID and Permissions.")
else:
    st.header("Please Login to View Your Portfolio")
    st.info("New here? Use the sidebar to create an account and link your Google Sheet.")
