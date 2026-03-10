import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
import datetime

# 1. Database Connection
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. THE FIX: DELETE CALLBACK ---
def delete_user_permanently(target_user):
    # 1. Clear portfolio first
    supabase.table("portfolio").delete().eq("username", target_user).execute()
    # 2. Delete user
    supabase.table("users").delete().eq("username", target_user).execute()
    # 3. Success message
    st.toast(f"User {target_user} deleted successfully.")
    # 4. FORCE REFRESH to kill the popover state
    st.rerun()

# 3. Page Config
st.set_page_config(page_title="GSE Intelligence", page_icon="🏦")
st.title("🏦 GSE Intelligence")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# --- LOGIN / REGISTRATION ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    with tab1:
        u = st.text_input("Username", key="login_u").lower().strip()
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("Sign In"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
            if res.data:
                now = datetime.datetime.now().isoformat()
                supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("Invalid Credentials")
    with tab2:
        with st.form("reg_form", clear_on_submit=True):
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if new_u and new_p:
                    supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                    st.success("User Registered!")

# --- LOGGED IN CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    st.sidebar.title(f"👋 {st.session_state.username}")
    menu = ["My Portfolio", "Admin Panel"] if is
