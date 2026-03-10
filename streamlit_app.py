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

# 2. Page Config & State
st.set_page_config(page_title="GSE Intelligence", page_icon="🏦")
st.title("🏦 GSE Intelligence")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'list_version' not in st.session_state:
    st.session_state.list_version = 0

# --- 3. DELETE CALLBACK ---
def handle_user_deletion(username_to_del):
    try:
        supabase.table("portfolio").delete().eq("username", username_to_del).execute()
        supabase.table("users").delete().eq("username", username_to_del).execute()
        st.session_state.list_version += 1
        st.toast(f"✅ User '{username_to_del}' removed.")
    except Exception:
        st.error("⚠️ Could not delete user.")

# --- LOGIN / REGISTRATION ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        u = st.text_input("Username", key="login_u").lower().strip()
        p = st.text_input("Password", type="password", key="login_p")
        
        col_login, col_forgot = st.columns([1, 2])
        
        if col_login.button("Sign In"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
            if res.data:
                now = datetime.datetime.now().isoformat()
                supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("❌ Incorrect username or password.")
        
        # --- NEW: FORGOT PASSWORD SECTION ---
        with col_forgot.popover("Forgot Password?"):
            st.write("### Reset Password")
            st.info("For security, password resets are handled by the administrator.")
            reset_user = st.text_input("Enter your username to request a reset").lower().strip()
            if st.button("Submit Request"):
                if reset_user:
                    st.success(f"Request sent for {reset_user}. Please contact the Admin at support@gse-intel.com.")
                else:
                    st.warning("Please enter your username.")

    with tab2:
        with st.form("reg_form", clear_on_submit=True):
            st.write("### Personal Information")
            col_fn, col_ln = st.columns(2)
            f_name = col_fn.text_input("First Name")
            l_name = col_ln.text_input("Last Name")
            o_name = st.text_input("Other Name (Optional)")
            
            col_dob, col_em = st.columns(2)
            dob = col_dob.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            email = col_em.text_input("Email Address")

            st.write("### Contact Details")
            col_cc, col_ph = st.columns([1, 3])
            # Added a few more common codes; you can expand this list
            country_codes = ["+233 (GH)", "+1 (US)", "+44 (UK)", "+234 (NG)", "+254 (KE)", "+36 (HU)"]
            c_code = col_cc.selectbox("Code", country_codes)
            phone = col_ph.text_input("Phone Number")
            
            st.divider()
            st.write("### Account Credentials")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Register"):
                required = [f_name, l_name, email, phone, new_u, new_p]
                if not all(required):
                    st.warning("All fields are required except 'Other Name'.")
                else:
                    try:
                        user_data = {
                            "username": new_u,
                            "password": make_hashes(new_p),
                            "first_name": f_name,
                            "last_name": l_name,
                            "other_name": o_name if o_name else None,
                            "dob": str(dob),
                            "email": email,
                            "phone_number": f"{c_code} {phone}"
                        }
                        supabase.table("users").insert(user_data).execute()
                        st.success("🎉 Registration successful! Please log in.")
                    except Exception as e:
                        st.error("🚫 Username or Email already exists.")

# --- LOGGED IN CONTENT ---
else:
    # (Rest of your Admin/Portfolio code remains the same)
    st.sidebar.title(f"👋 {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    st.write("Welcome to your dashboard!")
