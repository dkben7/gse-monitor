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

# This CSS centers the login box and styles the metrics
st.markdown("""
    <style>
    .stApp { max-width: 800px; margin: 0 auto; }
    [data-testid="stMetric"] { background-color: #1e1e1e; border-radius: 10px; padding: 15px; border: 1px solid #333; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Initialize login state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. CHECK LOGIN STATUS (GATEKEEPER) ---
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 4, 1])
    with col:
        st.title("🏦 GSE Intelligence")
        # THESE ARE THE TABS YOU WERE LOOKING FOR
        tab1, tab2 = st.tabs(["Login", "Create Account"])
        
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
                    st.error("Invalid Username or Password")
        
        with tab2:
            # UPDATED: We use keys here so we can clear them after registration
            new_u = st.text_input("New Username", key="reg_user").lower().strip()
            new_p = st.text_input("New Password", type="password", key="reg_pass")
            
            if st.button("Register"):
                if new_u and new_p:
                    try:
                        supabase.table("users").insert({
                            "username": new_u, 
                            "password": make_hashes(new_p)
                        }).execute()
                        
                        # CLEAR THE DATA: Reset the session state keys
                        st.session_state["reg_user"] = ""
                        st.session_state["reg_pass"] = ""
                        
                        st.success("Account created! Now switch to the Login tab.")
                        st.rerun() # Refresh to show empty boxes
                    except:
                        st.error("Username already taken.")
                else:
                    st.warning("Please fill in both fields.")

# --- 4. THE MAIN DASHBOARD (Only shows if logged_in is True) ---
else:
    with st.sidebar:
        st.header(f"👋 {st.session_state.username.title()}")
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.title("📈 Portfolio Dashboard")

    # Add Stock Section
    with st.expander("➕ Add New Transaction"):
        c1, c2, c3 = st.columns(3)
        tick = c1.text_input("Ticker").upper().strip()
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

    # Load and Display Data
    res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # Filter Zeros and Title Case
        df = df[df['change'] != 0]
        df['ticker'] = df['ticker'].str.title()

        for i, row in df.iterrows():
            cols = st.columns([3, 2, 1])
            cols[0].write(f"**{row['ticker']}** ({row['shares']:,} shares)")
            color = "green" if row['change'] > 0 else "red"
            cols[1].write(f":{color}[{row['change']:+.2f}%]")
            
            if cols[2].button("🗑️", key=f"del_{row['id']}"):
                supabase.table("portfolio").delete().eq("id", row['id']).execute()
                st.rerun()
    else:
        st.info("No stocks yet. Use the expander above to add one!")
