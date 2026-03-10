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
        if st.button("Sign In"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
            if res.data:
                now = datetime.datetime.now().isoformat()
                supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("❌ Incorrect username or password.")

    with tab2:
        with st.form("reg_form", clear_on_submit=True):
            st.write("### Personal Information")
            col1, col2 = st.columns(2)
            f_name = col1.text_input("First Name")
            l_name = col2.text_input("Last Name")
            
            o_name = st.text_input("Other Name (Optional)")
            
            col3, col4 = st.columns(2)
            dob = col3.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            email = col4.text_input("Email Address")
            
            st.divider()
            st.write("### Account Credentials")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Register"):
                # Basic Validation
                if not (f_name and l_name and email and new_u and new_p):
                    st.warning("Please fill in all required fields.")
                else:
                    try:
                        # Prepare data for Supabase
                        user_data = {
                            "username": new_u,
                            "password": make_hashes(new_p),
                            "first_name": f_name,
                            "last_name": l_name,
                            "other_name": o_name if o_name else None,
                            "dob": str(dob),
                            "email": email
                        }
                        supabase.table("users").insert(user_data).execute()
                        st.success("🎉 Account created! Please log in.")
                    except Exception as e:
                        if "duplicate key" in str(e).lower():
                            st.error("🚫 Username or Email already exists.")
                        else:
                            st.error("🚫 Registration failed. Check your database schema.")

# --- LOGGED IN CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    st.sidebar.title(f"👋 {st.session_state.username}")
    page = st.sidebar.radio("Navigation", ["My Portfolio", "Admin Panel"] if is_admin else ["My Portfolio"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if page == "Admin Panel" and is_admin:
        st.subheader("🛡️ Admin Control Panel")
        # Fetching more columns now
        user_res = supabase.table("users").select("*").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            # Expanded View for Admin
            for i, row in user_df.iterrows():
                with st.expander(f"👤 {row['first_name']} {row['last_name']} (@{row['username']})"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Email:** {row['email']}")
                    c1.write(f"**DOB:** {row['dob']}")
                    c2.write(f"**Joined:** {pd.to_datetime(row['created_at']).strftime('%Y-%m-%d')}")
                    
                    if row['username'] != "admin":
                        v = st.session_state.list_version
                        if st.button(f"🗑️ Delete {row['username']}", key=f"del_{row['username']}_{v}"):
                            handle_user_deletion(row['username'])
                            st.rerun()
        else:
            st.write("No users found.")
    else:
        st.write("### 📈 Portfolio Content")
