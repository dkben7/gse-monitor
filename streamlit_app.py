import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
import datetime
import random
import string

# --- 1. DATABASE CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def generate_temp_password(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# --- 2. COUNTRY DATA ---
COUNTRY_DATA = {"Ghana": "+233", "Hungary": "+36", "United States": "+1", "United Kingdom": "+44"} # [Truncated for brevity in display, keep your full list here]
code_options = [f"{name} ({code})" for name, code in sorted(COUNTRY_DATA.items())]

# --- 3. PAGE CONFIG & STATE ---
st.set_page_config(page_title="GSE Intelligence", page_icon="🏦", layout="centered")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'must_reset' not in st.session_state:
    st.session_state.must_reset = False

# --- 4. AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
    st.title("🏦 GSE Intelligence")
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            u = st.text_input("Username", key="login_u").lower().strip()
            p = st.text_input("Password", type="password", key="login_p")
            
            if st.button("Sign In", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    user_record = res.data[0]
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    # Check if this user is flagged for a mandatory reset
                    st.session_state.must_reset = user_record.get('must_reset', False)
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password.")
            
            st.write("") 
            # Updated Forgot Password Logic
            with st.popover("*Forgot Password?*", use_container_width=True):
                st.write("### Reset Request")
                reset_u = st.text_input("Enter Username", key="reset_u_field").lower().strip()
                if st.button("Send Temporary Password"):
                    check = supabase.table("users").select("email").eq("username", reset_u).execute()
                    if check.data:
                        temp_pass = generate_temp_password()
                        # Update DB with temp password and set the reset flag
                        supabase.table("users").update({
                            "password": make_hashes(temp_pass),
                            "must_reset": True
                        }).eq("username", reset_u).execute()
                        
                        st.success(f"Temporary password generated for {check.data[0]['email']}")
                        st.code(temp_pass)
                        st.info("Normally this would be sent via email. Use this code to log in now.")
                    else:
                        st.error("Username not found.")

    with tab2:
        # [Keep your existing Registration Form Code here]
        pass

# --- 5. MANDATORY PASSWORD RESET OVERLAY ---
elif st.session_state.must_reset:
    st.title("🔒 Security Update Required")
    st.warning("You are using a temporary password. You must create a new one to continue.")
    
    _, center_reset, _ = st.columns([1, 2, 1])
    with center_reset:
        new_p = st.text_input("New Password", type="password")
        conf_p = st.text_input("Confirm New Password", type="password")
        
        if st.button("Update Password & Login"):
            if new_p == conf_p and len(new_p) > 5:
                supabase.table("users").update({
                    "password": make_hashes(new_p),
                    "must_reset": False
                }).eq("username", st.session_state.username).execute()
                st.session_state.must_reset = False
                st.success("Password updated!")
                st.rerun()
            else:
                st.error("Passwords must match and be at least 6 characters.")

# --- 6. MAIN APPLICATION CONTENT ---
else:
    st.sidebar.title(f"👋 {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.write("### Welcome to the Secure Dashboard")
