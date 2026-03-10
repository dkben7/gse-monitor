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

# 3. Session State
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
                st.error("Invalid Username or Password")

    with tab2:
        with st.form("reg_form", clear_on_submit=True):
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Register"):
                if new_u and new_p:
                    try:
                        supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                        st.success("Account created! Switch to Login tab.")
                    except:
                        st.error("Registration failed. User may already exist.")

# --- LOGGED IN CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    st.sidebar.title(f"👋 {st.session_state.username}")
    menu = ["My Portfolio", "Admin Panel"] if is_admin else ["My Portfolio"]
    page = st.sidebar.radio("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # --- ADMIN PANEL ---
    if page == "Admin Panel" and is_admin:
        st.subheader("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("username, created_at, last_login").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.write(f"Total Members: {len(user_df)}")
            
            # Header Row
            h1, h2, h3, h4 = st.columns([2, 2, 2, 1])
            h1.write("**Username**"); h2.write("**Joined**"); h3.write("**Last Login**"); h4.write("**Action**")
            st.divider()

            for i, row in user_df.iterrows():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(row['username'])
                c2.write(pd.to_datetime(row['created_at']).strftime('%Y-%m-%d'))
                
                last_seen = pd.to_datetime(row['last_login']).strftime('%b %d, %H:%M') if row['last_login'] else "Never"
                c3.write(last_seen)
                
                if row['username'] != "admin":
                    # The Popover
                    with c4.popover("🗑️"):
                        st.write(f"Delete {row['username']}?")
                        # Important: Using a unique key and st.rerun() to force the UI to reset
                        if st.button("Confirm", key=f"del_btn_{row['username']}"):
                            supabase.table("portfolio").delete().eq("username", row['username']).execute()
                            supabase.table("users").delete().eq("username", row['username']).execute()
                            st.rerun()
                else:
                    c4.write("👑")

    # --- PORTFOLIO PAGE ---
    else:
        st.subheader("📈 My Portfolio")
        
        # Add Entry
        with st.expander("➕ Add Transaction"):
            c1, c2, c3 = st.columns(3)
            tick = c1.text_input("Ticker").upper().strip()
            sh = c2.number_input("Shares", min_value=0.0)
            ch = c3.number_input("Daily Change", format="%.2f")
            
            if st.button("Save"):
                if tick:
                    supabase.table("portfolio").insert({
                        "username": st.session_state.username, 
                        "ticker": tick, "shares": sh, "change": ch
                    }).execute()
                    st.rerun()

        # List Portfolio
        p_res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
        pdf = pd.DataFrame(p_res.data)
        if not pdf.empty:
            st.divider()
            for i, row in pdf.iterrows():
                cols = st.columns([4, 2, 1])
                cols[0].write(f"**{row['ticker']}** | {row['shares']:,} sh")
                clr = "green" if row['change'] > 0 else "red"
                cols[1].write(f":{clr}[{row['change']:+.2f}%]")
                
                with cols[2].popover("🗑️"):
                    if st.button("Delete", key=f"pdel_{row['id']}"):
                        supabase.table("portfolio").delete().eq("id", row['id']).execute()
                        st.rerun()
