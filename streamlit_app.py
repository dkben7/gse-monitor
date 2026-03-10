import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib

# --- 1. DATABASE CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="GSE Pro Monitor", layout="wide")

st.markdown("""
    <style>
    .stApp { max-width: 900px; margin: 0 auto; }
    [data-testid="stMetric"] { background-color: #1e1e1e; border-radius: 10px; padding: 15px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 12px; }
    .delete-btn>button { background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. LOGIN & REGISTRATION GATE ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.title("🏦 GSE Intelligence")
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            u = st.text_input("Username", key="l_u").lower().strip()
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("Sign In"):
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.
