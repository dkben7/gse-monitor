import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib

# --- 1. DATABASE CONNECTION ---
# These pull from your Streamlit Cloud Secrets
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="GSE Pro Monitor", layout="wide")

# Custom CSS for better mobile/dark mode visibility
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
        if is_admin:
            page = st.radio("Navigation", ["My Portfolio", "Admin Panel"])
        else:
            page = "My Portfolio"
        
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    # --- ADMIN PANEL PAGE ---
    if is_admin and page == "Admin Panel":
        st.title("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("username, created_at").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.metric("Total Users", len(user_df))
            for i, row in user_df.iterrows():
                c1, c2, c3 = st.columns([3, 3, 2])
                c1.write(f"**{row['username']}**")
                c2.write(f"Joined: {pd.to_datetime(row['created_at']).date()}")
                if row['username'] != ADMIN_USERNAME:
                    if c3.button("Delete", key=f"del_u_{row['username']}"):
                        supabase.table("portfolio").delete().eq("username", row['username']).execute()
                        supabase.table("users").delete().eq("username", row['username']).execute()
                        st.rerun()
        else:
            st.info("No registered users found.")

    # --- MY PORTFOLIO PAGE ---
    else:
        st.title("📈 My Portfolio")
        
        with st.expander("➕ Add Transaction"):
            c1, c2, c3 = st.columns(3)
            tick = c1.text_input("Ticker").upper().strip()
            sh = c2.number_input("Shares", min_value=0.0)
            ch = c3.number_input("Daily Change", format="%.2f")
            if st.button("Save Transaction"):
                if tick:
                    supabase.table("portfolio").insert({
                        "username": st.session_state.username, 
                        "ticker": tick, 
                        "shares": sh, 
                        "change": ch
                    }).execute()
                    st.success(f"Added {tick}!")
                    st.rerun()

        # Load Portfolio Data
        res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            df['ticker'] = df['ticker'].str.upper()
            for i, row in df.iterrows():
                with st.container():
                    cols = st.columns([4, 2, 1])
                    cols[0].write(f"**{row['ticker']}** | {row['shares']:,} shares")
                    color = "green" if row['change'] > 0 else "red"
                    cols[1].write(f":{color}[{row['change']:+.2f}%]")
                    if cols[2].button("🗑️", key=f"p_del_{row['id']}"):
                        supabase.table("portfolio").delete().eq("id", row['id']).execute()
                        st.rerun()
        else:
            st.info("Your portfolio is currently empty.")
