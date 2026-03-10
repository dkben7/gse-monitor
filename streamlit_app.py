import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib

# --- 1. DATABASE CONNECTION ---
# These pull directly from the Secrets you just saved!
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. UI SETTINGS ---
st.set_page_config(page_title="GSE Pro Monitor", layout="wide")

# Custom CSS for Mobile-Friendly look
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    [data-testid="stMetric"] { background-color: #1e1e1e; border-radius: 10px; padding: 15px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. CENTERED LOGIN PAGE ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.title("🏦 GSE Intelligence")
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
        with tab1:
            u = st.text_input("Username").lower().strip()
            p = st.text_input("Password", type="password")
            if st.button("Sign In"):
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
        
        with tab2:
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            if st.button("Register"):
                try:
                    supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                    st.success("Account created! You can now login.")
                except:
                    st.error("Username already taken.")

# --- 4. THE MAIN DASHBOARD ---
else:
    with st.sidebar:
        st.write(f"Logged in as: **{st.session_state.username.title()}**")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📈 Portfolio Dashboard")

    # Add Stock Section
    with st.expander("➕ Add New Transaction"):
        c1, c2, c3 = st.columns(3)
        tick = c1.text_input("Ticker (e.g. MTN)").upper().strip()
        sh = c2.number_input("Shares", min_value=0.0)
        ch = c3.number_input("Daily Change %", format="%.2f")
        
        if st.button("Save to Cloud"):
            if tick:
                supabase.table("portfolio").insert({
                    "username": st.session_state.username,
                    "ticker": tick,
                    "shares": sh,
                    "change": ch
                }).execute()
                st.success(f"Added {tick}!")
                st.rerun()

    # Load Data
    res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # Filter Ghost Zeros & Capitalize
        df = df[df['change'] != 0]
        df['ticker'] = df['ticker'].str.title()

        st.subheader("Current Holdings")
        for i, row in df.iterrows():
            with st.container():
                cols = st.columns([3, 2, 1])
                cols[0].write(f"**{row['ticker']}**")
                cols[0].caption(f"{row['shares']:,} shares")
                
                color = "green" if row['change'] > 0 else "red"
                cols[1].write(f":{color}[{row['change']:+.2f}%]")
                
                if cols[2].button("🗑️", key=f"del_{row['id']}"):
                    supabase.table("portfolio").delete().eq("id", row['id']).execute()
                    st.rerun()
    else:
        st.info("Your portfolio is empty. Add a stock above to get started!")
