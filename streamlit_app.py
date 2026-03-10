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
if 'sys_msg' not in st.session_state:
    st.session_state.sys_msg = None

# Show global system messages (Success/Error)
if st.session_state.sys_msg:
    st.success(st.session_state.sys_msg)
    st.session_state.sys_msg = None # Clear it after showing

# --- 3. CALLBACK FUNCTIONS ---
# These run BEFORE the rest of the page loads, keeping the UI perfectly in sync
def delete_user_cb(target_username):
    try:
        supabase.table("portfolio").delete().eq("username", target_username).execute()
        supabase.table("users").delete().eq("username", target_username).execute()
        st.session_state.sys_msg = f"User {target_username} was successfully deleted."
    except Exception as e:
        st.session_state.sys_msg = f"Error: Failed to delete user {target_username}."

def delete_stock_cb(stock_id):
    try:
        supabase.table("portfolio").delete().eq("id", stock_id).execute()
        st.session_state.sys_msg = "Stock successfully removed from portfolio."
    except Exception as e:
        st.session_state.sys_msg = "Error: Failed to delete stock."

# --- LOGIN / REGISTRATION ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        u = st.text_input("Username", key="login_u").lower().strip()
        p = st.text_input("Password", type="password", key="login_p")
        
        if st.button("Sign In"):
            try:
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    now = datetime.datetime.now().isoformat()
                    supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            except Exception as e:
                st.error("Login service unavailable.")

    with tab2:
        with st.form("registration_form", clear_on_submit=True):
            st.write("### Create a New Account")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            submit_reg = st.form_submit_button("Register")
        
        if submit_reg:
            if new_u and new_p:
                try:
                    supabase.table("users").insert({"username": new_u, "password": make_hashes(new_p)}).execute()
                    st.success(f"Account '{new_u}' created! You can now log in.")
                    st.balloons()
                except Exception as e:
                    if "duplicate key" in str(e).lower():
                        st.error("That username is already taken.")
                    else:
                        st.error("Registration failed.")
            else:
                st.warning("Please fill in both fields.")

# --- LOGGED IN CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    
    st.sidebar.title(f"👋 Welcome, {st.session_state.username}")
    menu = ["My Portfolio"]
    if is_admin:
        menu.append("Admin Panel")
    
    page = st.sidebar.radio("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    # --- ADMIN PANEL ---
    if page == "Admin Panel" and is_admin:
        st.title("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("username, created_at, last_login").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.metric("Total Members", len(user_df))
            
            h1, h2, h3, h4 = st.columns([2, 2, 2, 1])
            h1.write("**Username**")
            h2.write("**Joined**")
            h3.write("**Last Login**")
            h4.write("**Action**")
            st.divider()

            for i, row in user_df.iterrows():
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(f"**{row['username']}**")
                
                join_date = pd.to_datetime(row['created_at']).strftime('%Y-%m-%d')
                last_seen = pd.to_datetime(row['last_login']).strftime('%b %d, %H:%M') if pd.notnull(row['last_login']) else "Never"
                
                c2.write(join_date)
                c3.write(last_seen)
                
                if row['username'] != "admin":
                    with c4.popover("🗑️"):
                        st.write(f"Delete **{row['username']}**?")
                        # We pass the callback directly to the button
                        st.button("Yes, delete", key=f"conf_del_{row['username']}", on_click=delete_user_cb, args=(row['username'],))
                else:
                    c4.write("👑")
        else:
            st.write("No users registered yet.")

    # --- PORTFOLIO PAGE ---
    else:
        st.title("📈 My Portfolio")
        
        with st.expander("🔑 Forgot Password?"):
            st.info("Password resets are handled manually. Contact the administrator.")

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
                            "ticker": tick, "shares": sh, "change": ch
                        }).execute()
                        st.session_state.sys_msg = f"Added {tick}!"
                        st.rerun()
                    except Exception as e:
                        st.error("Unable to save.")
                else:
                    st.warning("Please enter a Ticker.")

        res = supabase.table("portfolio").select("*").eq("username", st.session_state.username).execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            st.divider()
            for i, row in df.iterrows():
                cols = st.columns([4, 2, 1])
                cols[0].write(f"**{row['ticker']}** | {row['shares']:,} sh")
                clr = "green" if row['change'] > 0 else "red"
                cols[1].write(f":{clr}[{row['change']:+.2f}%]")
                
                with cols[2].popover("🗑️"):
                    st.write("Delete stock?")
                    # Passed the callback directly to the button
                    st.button("Yes", key=f"conf_p_{row['id']}", on_click=delete_stock_cb, args=(row['id'],))
