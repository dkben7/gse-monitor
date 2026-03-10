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

# 2. Page Config
st.set_page_config(page_title="GSE Intelligence", page_icon="🏦")
st.title("🏦 GSE Intelligence")

# 3. Session State Initialization
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
            try:
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    # Update Last Login
                    now = datetime.datetime.now().isoformat()
                    supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                    
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            except Exception as e:
                st.error("Login service unavailable.")

    with tab2:
        # Form handles the "clear_on_submit" automatically
        with st.form("registration_form", clear_on_submit=True):
            st.write("### Create a New Account")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            submit_reg = st.form_submit_button("Register")
        
        if submit_reg:
            if new_u and new_p:
                try:
                    supabase.table("users").insert({
                        "username": new_u, 
                        "password": make_hashes(new_p)
                    }).execute()
                    st.success(f"Account '{new_u}' created! You can now log in.")
                    st.balloons()
                except Exception as e:
                    if "duplicate key" in str(e).lower():
                        st.error("That username is already taken.")
                    else:
                        st.error("Registration failed. Please try again.")
            else:
                st.warning("Please fill in both fields.")

# --- LOGGED IN CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    
    # Sidebar Navigation
    st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
    menu = ["My Portfolio"]
    if is_admin:
        menu.append("Admin Panel")
    
    page = st.sidebar.radio("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    # --- ADMIN PANEL ---
    if page == "Admin Panel" and is_admin:
        st.title("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("username, created_at, last_login").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.metric("Total Members", len(user_df))
            h1, h2
