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

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None

# --- CALLBACKS ---
def delete_user_cb(target_username):
    supabase.table("portfolio").delete().eq("username", target_username).execute()
    supabase.table("users").delete().eq("username", target_username).execute()
    st.toast(f"User {target_username} deleted")

def delete_stock_cb(stock_id):
    supabase.table("portfolio").delete().eq("id", stock_id).execute()
    st.toast("Stock removed")

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
                st.error("Invalid credentials")
    with tab2:
        with st.form("reg_form", clear_on_submit=True):
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if new_u and new_p:
                    supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                    st.success("Account created!")

# --- LOGGED IN CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    st.sidebar.title(f"👋 {st.session_state.username}")
    page = st.sidebar.radio("Navigation", ["My Portfolio", "Admin Panel"] if is_admin else ["My Portfolio"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- ADMIN PANEL FRAGMENT ---
    if page == "Admin Panel" and is_admin:
        st.title("🛡️ Admin Control Panel")
        
        @st.fragment
        def show_user_management():
            user_res = supabase.table("users").select("username, created_at, last_login").execute()
            df = pd.DataFrame(user_res.data)
            if not df.empty:
                st.metric("Total Members", len(df))
                h = st.columns([2, 2, 2, 1])
                h[0].write("**Username**"); h[1].write("**Joined**"); h[2].write("**Last Login**"); h[3].write("**Action**")
                st.divider()
                for i, row in df.iterrows():
                    c = st.columns([2, 2, 2, 1])
                    c[0].write(row['username'])
                    c[1].write(pd.to_datetime(row['created_at']).strftime('%Y-%m-%d'))
                    last = pd.to_datetime(row['last_login']).strftime('%b %d, %H:%M') if row['last_login'] else "Never"
                    c[2].write(last)
                    if row['username'] != "admin":
                        with c[3].popover("🗑️"):
                            st.write(f"Confirm delete {row['username']}?")
                            st.button("Yes, delete", key=f"del_{row['username']}", on_click=delete_user_cb, args=(row['username'],))
                    else:
                        c[3].write("👑")
        
        show_user_management()

    # --- PORTFOLIO FRAGMENT ---
    else:
        st.title("📈 My Portfolio")
        
        with st.expander("➕ Add Transaction"):
            c1, c2, c3 = st.columns(3)
            tick = c1.text_input("Ticker").upper()
            sh = c2.number_input("Shares", min_value=0.0)
            ch = c3.
