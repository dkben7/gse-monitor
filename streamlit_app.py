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
            u = st.text_input("Username", key="login_user").lower().strip()
            p = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Sign In"):
                try:
                    res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                    if res.data:
                        # NEW: Update the last_login timestamp in the database
                        import datetime
                        now = datetime.datetime.now().isoformat()
                        supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                        
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password")
                except Exception as e:
                    st.error("Login service unavailable.")
                    if st.session_state.get("username") == "admin":
                        st.info(f"🛡️ Admin Dev Info: {e}")
        
        with tab2:
            new_u = st.text_input("New Username", key="reg_u").lower().strip()
            new_p = st.text_input("New Password", type="password", key="reg_p")
            
            if st.button("Register"):
                if new_u and new_p:
                    try:
                        # 1. Save to Database
                        supabase.table("users").insert({
                            "username": new_u, 
                            "password": make_hashes(new_p)
                        }).execute()
                        
                        st.success(f"Account for '{new_u}' created! Switch to the Login tab.")

                        # 2. CLEAR THE WIDGETS
                        # Deleting the keys from session state resets the text_input boxes
                        del st.session_state["reg_u"]
                        del st.session_state["reg_p"]

                        # 3. Refresh to show empty boxes
                        st.rerun()

                    except Exception as e:
                        if "duplicate key" in str(e).lower():
                            st.error(f"The username '{new_u}' is already taken.")
                        else:
                            st.error("Registration failed. Please try again.")
                        
                        if st.session_state.get("username") == "admin":
                            st.info(f"🛡️ Admin Dev Info: {e}")
                else:
                    st.warning("Please fill in both fields.")
                    
# --- 4. THE DASHBOARD ---
else:
    ADMIN_USERNAME = "admin" 
    is_admin = st.session_state.username == ADMIN_USERNAME

    with st.sidebar:
        st.header(f"👋 {st.session_state.username.title()}")
        page = st.radio("Navigation", ["My Portfolio", "Admin Panel"]) if is_admin else "My Portfolio"
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    if page == "Admin Panel" and is_admin:
        st.title("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("username, created_at, last_login").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.metric("Total Members", len(user_df))
            
            # Format the dates for a cleaner look
            user_df['created_at'] = pd.to_datetime(user_df['created_at']).dt.strftime('%Y-%m-%d')
            user_df['last_login'] = pd.to_datetime(user_df['last_login']).dt.strftime('%b %d, %H:%M')
            
            # Display as a clean table
            st.table(user_df[['username', 'created_at', 'last_login']])
        else:
            st.write("No users registered yet.")
    else:
        st.title("📈 My Portfolio")
        with st.expander("➕ Add Transaction"):
            c1, c2, c3 = st.columns(3)
            tick = c1.text_input("Ticker").upper().strip()
            sh = c2.number_input("Shares", min_value=0.0)
            ch = c3.number_input("Daily Change", format="%.2f")
            
            if st.button("Save Transaction"):
                if tick:
                    try:
                        supabase.table("portfolio").insert({
                            "username": st.session_state.username, 
                            "ticker": tick, 
                            "shares": sh, 
                            "change": ch
                        }).execute()
                        st.success(f"Successfully added {tick} to your portfolio!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error("Unable to save transaction. Please try again.")
                        
                        # Admin Debug Info
                        if st.session_state.get("username") == "admin":
                            st.info(f"🛡️ Admin Dev Info: {e}")
                else:
                    st.warning("Please enter a Ticker symbol.")

        res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            for i, row in df.iterrows():
                cols = st.columns([4, 2, 1])
                cols[0].write(f"**{row['ticker']}** | {row['shares']:,} sh")
                clr = "green" if row['change'] > 0 else "red"
                cols[1].write(f":{clr}[{row['change']:+.2f}%]")
                if cols[2].button("🗑️", key=f"p_{row['id']}"):
                    supabase.table("portfolio").delete().eq("id", row['id']).execute()
                    st.rerun()
