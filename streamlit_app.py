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
            col_fn, col_ln = st.columns(2)
            f_name = col_fn.text_input("First Name")
            l_name = col_ln.text_input("Last Name")
            
            o_name = st.text_input("Other Name (Optional)")
            
            col_dob, col_em = st.columns(2)
            dob = col_dob.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            email = col_em.text_input("Email Address")

            # --- Phone Number Section ---
            st.write("### Contact Details")
            col_cc, col_ph = st.columns([1, 2])
            # Common country codes - you can add more to this list
            country_codes = ["+233 (GH)", "+36 (HU)", "+1 (US)", "+44 (UK)", "+234 (NG)", "+254 (KE)"]
            c_code = col_cc.selectbox("Code", country_codes)
            phone = col_ph.text_input("Phone Number")
            
            st.divider()
            st.write("### Account Credentials")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Register"):
                # "Other Name" is the ONLY optional field now
                required_fields = [f_name, l_name, email, phone, new_u, new_p]
                
                if not all(required_fields):
                    st.warning("Please fill in all required fields (Only 'Other Name' is optional).")
                else:
                    try:
                        full_phone = f"{c_code} {phone}"
                        user_data = {
                            "username": new_u,
                            "password": make_hashes(new_p),
                            "first_name": f_name,
                            "last_name": l_name,
                            "other_name": o_name if o_name else None,
                            "dob": str(dob),
                            "email": email,
                            "phone_number": full_phone
                        }
                        supabase.table("users").insert(user_data).execute()
                        st.success("🎉 Account created! Log in to continue.")
                    except Exception as e:
                        if "duplicate key" in str(e).lower():
                            st.error("🚫 Username, Email, or Phone already exists.")
                        else:
                            st.error("🚫 Registration failed. Check database columns.")

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
        user_res = supabase.table("users").select("*").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            for i, row in user_df.iterrows():
                # Display all new info in the admin expander
                display_name = f"{row['first_name']} {row['last_name']}"
                if row['other_name']:
                    display_name = f"{row['first_name']} {row['other_name']} {row['last_name']}"
                
                with st.expander(f"👤 {display_name} (@{row['username']})"):
                    c1, c2 = st.columns(2)
                    c1.write(f"**Email:** {row['email']}")
                    c1.write(f"**Phone:** {row['phone_number']}")
                    c2.write(f"**DOB:** {row['dob']}")
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
