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
            u = st.text_input("Username", key="l_u").lower().strip()
            p = st.text_input("Password", type="password", key="l_p")
            
            if st.button("Sign In"):
                # ... (your existing login logic) ...
                pass

            # Forgot Password logic
            st.divider()
            with st.expander("🔑 Forgot Password?"):
                st.write("For security, password resets are handled manually.")
                st.info("Please contact the administrator (admin@youruniversity.edu) to reset your credentials.")
                
                # Optional: A 'Secret' way for the admin to reset it via code
                st.caption("Admin: You can reset passwords directly in the Supabase Table Editor by updating the 'password' column with a new hash.")
        
        with tab2:
            # We use a form with clear_on_submit=True
            # This is the only 100% reliable way to empty boxes in Streamlit
            with st.form("registration_form", clear_on_submit=True):
                st.write("### Create a New Account")
                new_u = st.text_input("New Username").lower().strip()
                new_p = st.text_input("New Password", type="password")
                submit_reg = st.form_submit_button("Register")
            
            if submit_reg:
                if new_u and new_p:
                    try:
                        # 1. Attempt the database insert
                        supabase.table("users").insert({
                            "username": new_u, 
                            "password": make_hashes(new_p)
                        }).execute()
                        
                        # 2. Success Feedback
                        st.success(f"Success! Account '{new_u}' created. You can now switch to the Login tab.")
                        st.balloons() # Visual confirmation that survives the state change
                        
                    except Exception as e:
                        error_text = str(e).lower()
                        if "duplicate key" in error_text:
                            st.error(f"The username '{new_u}' is already taken. Please try another.")
                        else:
                            st.error("Registration failed. Please try again.")
                        
                        # Admin Debug
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
        
        # 1. Fetch User Data
        user_res = supabase.table("users").select("username, created_at, last_login").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.metric("Total Members", len(user_df))
            
            # 2. Table Header
            h1, h2, h3, h4 = st.columns([2, 2, 2, 1])
            h1.write("**Username**")
            h2.write("**Joined**")
            h3.write("**Last Login**")
            h4.write("**Action**")
            st.divider()

            # 3. Dynamic User Rows
            for i, row in user_df.iterrows():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(f"**{row['username']}**")
                
                # Format Dates
                join_date = pd.to_datetime(row['created_at']).strftime('%Y-%m-%d')
                login_date = pd.to_datetime(row['last_login']).strftime('%b %d, %H:%M') if row['last_login'] else "Never"
                
                c2.write(join_date)
                c3.write(login_date)
                
                # Delete logic for Admin
                if row['username'] != "admin":
                    if c4.button("🗑️", key=f"del_{row['username']}"):
                        try:
                            # Delete portfolio first to avoid Foreign Key errors
                            supabase.table("portfolio").delete().eq("username", row['username']).execute()
                            # Delete user
                            supabase.table("users").delete().eq("username", row['username']).execute()
                            st.success(f"User {row['username']} deleted.")
                            st.rerun()
                        except Exception as e:
                            st.error("Delete failed.")
                            st.info(f"Dev Info: {e}")
                else:
                    c4.write("👑")
        else:
            st.write("No users registered yet.")

    # --- PORTFOLIO PAGE FOR REGULAR USERS ---
    else:
        st.title("📈 My Portfolio")
        
        # Password Reset Helper (Manual Admin Reset)
        with st.expander("🔑 Forgot Password?"):
            st.info("Password resets are handled manually for security. Please contact the administrator.")

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
                        st.success(f"Successfully added {tick}!")
                        st.rerun()
                    except Exception as e:
                        st.error("Unable to save transaction.")
                        if st.session_state.get("username") == "admin":
                            st.info(f"🛡️ Admin Dev Info: {e}")
                else:
                    st.warning("Please enter a Ticker symbol.")

        # Display Portfolio List
        res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            st.divider()
            for i, row in df.iterrows():
                cols = st.columns([4, 2, 1])
                cols[0].write(f"**{row['ticker']}** | {row['shares']:,} sh")
                clr = "green" if row['change'] > 0 else "red"
                cols[1].write(f":{clr}[{row['change']:+.2f}%]")
                if cols[2].button("🗑️", key=f"p_{row['id
