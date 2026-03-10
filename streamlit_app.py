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

# Initialize Session States
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0  # 0 for Login, 1 for Register

# --- 3. GATEKEEPER ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.title("🏦 GSE Intelligence")
        
        # We use a manual index so we can switch tabs programmatically
        tab_list = ["Login", "Create Account"]
        tab1, tab2 = st.tabs(tab_list)
        
        with tab1:
            u = st.text_input("Username", key="login_user").lower().strip()
            p = st.text_input("Password", type="password", key="login_pass")
            if st.button("Sign In"):
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with tab2:
            new_u = st.text_input("New Username", key="reg_user").lower().strip()
            new_p = st.text_input("New Password", type="password", key="reg_pass")
            
            if st.button("Register"):
                if new_u and new_p:
                    try:
                        supabase.table("users").insert({
                            "username": new_u, 
                            "password": make_hashes(new_p)
                        }).execute()
                        
                        # Clear inputs
                        st.session_state["reg_user"] = ""
                        st.session_state["reg_pass"] = ""
                        
                        st.success("Account created! Please log in now.")
                        # This stays on the Register tab but shows success. 
                        # To auto-switch, Streamlit requires a slightly more complex query param setup.
                    except:
                        st.error("Username already taken.")

# --- 4. THE MAIN DASHBOARD & ADMIN PAGE ---
else:
    # --- ADMIN CHECK ---
    # Replace 'your_username' with whatever username you registered for yourself
    is_admin = st.session_state.username == "admin" 

    with st.sidebar:
        st.header(f"👋 {st.session_state.username.title()}")
        
        page = st.radio("Navigation", ["My Portfolio", "Admin Panel"]) if is_admin else "My Portfolio"
        
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    if page == "Admin Panel" and is_admin:
        st.title("🛡️ Admin Control Panel")
        st.subheader("Registered Users")
        
        # Query all users but EXCLUDE the password column for security
        user_res = supabase.table("users").select("username, created_at").execute()
        user_df = pd.DataFrame(user_res.data)
        
        if not user_df.empty:
            user_df['created_at'] = pd.to_datetime(user_df['created_at']).dt.date
            st.table(user_df)
            st.metric("Total Members", len(user_df))
        else:
            st.write("No users registered yet.")

    else:
        st.title("📈 My Portfolio")
        # ... (Insert your portfolio 'Add Transaction' and 'Load Data' code here)
        # For brevity, use the logic from the previous snippet here.
