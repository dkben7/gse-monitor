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

# Custom Styling
st.markdown("""
    <style>
    .stApp { max-width: 900px; margin: 0 auto; }
    [data-testid="stMetric"] { background-color: #1e1e1e; border-radius: 10px; padding: 15px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. LOGIN & REGISTRATION ---
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
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        
        with tab2:
            new_u = st.text_input("New Username", key="reg_u").lower().strip()
            new_p = st.text_input("New Password", type="password", key="reg_p")
            if st.button("Register"):
                if new_u and new_p:
                    try:
                        supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                        st.session_state["reg_u"] = ""
                        st.session_state["reg_p"] = ""
                        st.success("Account created! You can now Login.")
                        st.rerun()
                    except:
                        st.error("Username taken.")

# --- 4. THE APP INTERIOR ---
else:
    # Set your admin username here
    ADMIN_USERNAME = "admin" 
    is_admin = st.session_state.username == ADMIN_USERNAME

    with st.sidebar:
        st.header(f"👋 {st.session_state.username.title()}")
        # Page navigation for Admin
        if is_admin:
            page = st.radio("Navigation", ["My Portfolio", "Admin Panel"])
        else:
            page = "My Portfolio"
        
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    # ADMIN PANEL PAGE
    if is_admin and page == "Admin Panel":
        st.title("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("username, created_at").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.metric("Total Users", len(user_df))
            for i, row in user_df.iterrows():
                c1, c2, c3 = st.columns([3, 3, 2])
                c1.write(f"**{row
