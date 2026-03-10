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

# --- 3. CLEAN DELETE CALLBACK ---
def handle_user_deletion(username_to_del):
    try:
        # We perform the delete inside a try block to catch any DB issues
        supabase.table("portfolio").delete().eq("username", username_to_del).execute()
        supabase.table("users").delete().eq("username", username_to_del).execute()
        st.session_state.list_version += 1
        st.toast(f"✅ User '{username_to_del}' removed.")
    except Exception:
        # If something fails, show a friendly message instead of a crash
        st.error("⚠️ Could not delete user. Please try again later.")

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
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if not new_u or not new_p:
                    st.warning("Please fill in both fields.")
                else:
                    try:
                        # Attempt to register
                        supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                        st.success("🎉 Account created! You can now switch to the Login tab.")
                    except Exception:
                        # This catches duplicate usernames or DB connection issues
                        st.error("🚫 That username is already taken. Please try a different one.")

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
        user_res = supabase.table("users").select("username, created_at, last_login").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            h = st.columns([2, 2, 2, 1])
            h[0].write("**Username**"); h[1].write("**Joined**"); h[2].write("**Last Login**"); h[3].write("**Action**")
            st.divider()

            for i, row in user_df.iterrows():
                c = st.columns([2, 2, 2, 1])
                c[0].write(row['username'])
                c[1].write(pd.to_datetime(row['created_at']).strftime('%Y-%m-%d'))
                last = pd.to_datetime(row['last_login']).strftime('%b %d, %H:%M') if row['last_login'] else "Never"
                c[2].write(last)
                
                if row['username'] != "admin":
                    v = st.session_state.list_version
                    with c[3].popover("🗑️", key=f"pop_{row['username']}_{v}"):
                        st.write(f"Permanently delete **{row['username']}**?")
                        st.button(
                            "Confirm Delete", 
                            key=f"btn_{row['username']}_{v}", 
                            on_click=handle_user_deletion, 
                            args=(row['username'],),
                            type="primary" # Makes the button red/prominent
                        )
                else:
                    c[3].write("👑")
    else:
        st.write("### 📈 Portfolio Content")
