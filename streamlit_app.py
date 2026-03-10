import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
import datetime
import random
import string

# --- 1. DATABASE CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def generate_temp_password(length=8):
    """Generates a random 8-character string for temporary login."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# --- 2. GLOBAL COUNTRY DATA ---
COUNTRY_DATA = {
    "Afghanistan": "+93", "Albania": "+355", "Algeria": "+213", "Andorra": "+376", "Angola": "+244",
    "Argentina": "+54", "Armenia": "+374", "Australia": "+61", "Austria": "+43", "Azerbaijan": "+994",
    "Bahamas": "+1-242", "Bahrain": "+973", "Bangladesh": "+880", "Barbados": "+1-246", "Belgium": "+32",
    "Belize": "+501", "Benin": "+229", "Bhutan": "+975", "Bolivia": "+591", "Bosnia": "+387",
    "Botswana": "+267", "Brazil": "+55", "Bulgaria": "+359", "Burkina Faso": "+226", "Burundi": "+257",
    "Cambodia": "+855", "Cameroon": "+237", "Canada": "+1", "Cape Verde": "+238", "Chad": "+235",
    "Chile": "+56", "China": "+86", "Colombia": "+57", "Congo": "+242", "Costa Rica": "+506",
    "Croatia": "+385", "Cuba": "+53", "Cyprus": "+357", "Czech Republic": "+420", "Denmark": "+45",
    "Djibouti": "+253", "Dominica": "+1-767", "Dominican Republic": "+1-809", "Ecuador": "+593", "Egypt": "+20",
    "El Salvador": "+503", "Estonia": "+372", "Ethiopia": "+251", "Fiji": "+679", "Finland": "+358",
    "France": "+33", "Gabon": "+241", "Gambia": "+220", "Georgia": "+995", "Germany": "+49",
    "Ghana": "+233", "Greece": "+30", "Grenada": "+1-473", "Guatemala": "+502", "Guinea": "+224",
    "Guyana": "+592", "Haiti": "+509", "Honduras": "+504", "Hong Kong": "+852", "Hungary": "+36",
    "Iceland": "+354", "India": "+91", "Indonesia": "+62", "Iran": "+98", "Iraq": "+964",
    "Ireland": "+353", "Israel": "+972", "Italy": "+39", "Jamaica": "+1-876", "Japan": "+81",
    "Jordan": "+962", "Kazakhstan": "+7", "Kenya": "+254", "Korea, North": "+850", "Korea, South": "+82",
    "Kuwait": "+965", "Kyrgyzstan": "+996", "Laos": "+856", "Latvia": "+371", "Lebanon": "+961",
    "Lesotho": "+266", "Liberia": "+231", "Libya": "+218", "Lithuania": "+370", "Luxembourg": "+352",
    "Malaysia": "+60", "Maldives": "+960", "Mali": "+223", "Malta": "+356", "Mexico": "+52",
    "Moldova": "+373", "Monaco": "+377", "Mongolia": "+976", "Montenegro": "+382", "Morocco": "+212",
    "Mozambique": "+258", "Myanmar": "+95", "Namibia": "+264", "Nepal": "+977", "Netherlands": "+31",
    "New Zealand": "+64", "Nicaragua": "+505", "Niger": "+227", "Nigeria": "+234", "Norway": "+47",
    "Oman": "+968", "Pakistan": "+92", "Panama": "+507", "Paraguay": "+595", "Peru": "+51",
    "Philippines": "+63", "Poland": "+48", "Portugal": "+351", "Qatar": "+974", "Romania": "+40",
    "Russia": "+7", "Rwanda": "+250", "Saudi Arabia": "+966", "Senegal": "+221", "Serbia": "+381",
    "Singapore": "+65", "Slovakia": "+421", "Slovenia": "+386", "South Africa": "+27", "Spain": "+34",
    "Sri Lanka": "+94", "Sudan": "+249", "Sweden": "+46", "Switzerland": "+41", "Syria": "+963",
    "Taiwan": "+886", "Tanzania": "+255", "Thailand": "+66", "Togo": "+228", "Trinidad & Tobago": "+1-868",
    "Tunisia": "+216", "Turkey": "+90", "Uganda": "+256", "Ukraine": "+380", "United Arab Emirates": "+971",
    "United Kingdom": "+44", "United States": "+1", "Uruguay": "+598", "Uzbekistan": "+998",
    "Venezuela": "+58", "Vietnam": "+84", "Yemen": "+967", "Zambia": "+260", "Zimbabwe": "+263"
}
code_options = [f"{name} ({code})" for name, code in sorted(COUNTRY_DATA.items())]

# --- 3. PAGE CONFIG & STATE ---
st.set_page_config(page_title="GSE Intelligence", page_icon="🏦", layout="centered")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'must_reset' not in st.session_state:
    st.session_state.must_reset = False
if 'list_version' not in st.session_state:
    st.session_state.list_version = 0

# --- 4. CALLBACK FUNCTIONS ---
def handle_user_deletion(username_to_del):
    try:
        supabase.table("portfolio").delete().eq("username", username_to_del).execute()
        supabase.table("users").delete().eq("username", username_to_del).execute()
        st.session_state.list_version += 1
        st.toast(f"✅ User '{username_to_del}' deleted.")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")
    st.rerun()

# --- 5. AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
    st.title("🏦 GSE Intelligence")
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        _, center_col, _ = st.columns([1, 2, 1])
        with center_col:
            u = st.text_input("Username", key="login_u").lower().strip()
            p = st.text_input("Password", type="password", key="login_p")
            
            if st.button("Sign In", use_container_width=True):
                res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
                if res.data:
                    user_data = res.data[0]
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.must_reset = user_data.get('must_reset', False)
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password.")
            
            # --- FORGOT PASSWORD (ITALICIZED) ---
            st.write("") 
            with st.popover("*Forgot Password?*", use_container_width=True):
                st.write("### Reset Request")
                reset_u = st.text_input("Username", key="reset_u_field").lower().strip()
                if st.button("Send Temporary Password"):
                    check = supabase.table("users").select("email").eq("username", reset_u).execute()
                    if check.data:
                        temp_pass = generate_temp_password()
                        supabase.table("users").update({
                            "password": make_hashes(temp_pass),
                            "must_reset": True
                        }).eq("username", reset_u).execute()
                        
                        st.success(f"Temp password generated for {check.data[0]['email']}")
                        st.code(temp_pass)
                        st.info("Log in with this code. You will be asked to change it immediately.")
                    else:
                        st.error("Username not found.")

    with tab2:
        with st.form("reg_form", clear_on_submit=True):
            st.write("### Personal Information")
            c1, c2 = st.columns(2)
            f_name = c1.text_input("First Name")
            l_name = c2.text_input("Last Name")
            o_name = st.text_input("Other Name (Optional)")
            
            c3, c4 = st.columns(2)
            dob = c3.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today())
            email = c4.text_input("Email Address")

            st.write("### Contact Details")
            c_cc, c_ph = st.columns([2, 3])
            try:
                def_idx = sorted(COUNTRY_DATA.keys()).index("Ghana")
            except:
                def_idx = 0
            selected_country = c_cc.selectbox("Country Code", code_options, index=def_idx)
            phone_body = c_ph.text_input("Phone Number")
            
            st.divider()
            st.write("### Account Credentials")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Register", use_container_width=True):
                required = [f_name, l_name, email, phone_body, new_u, new_p]
                if not all(required):
                    st.warning("All fields except 'Other Name' are required.")
                else:
                    try:
                        phone_code = selected_country.split('(')[-1].strip(')')
                        user_insert = {
                            "username": new_u, "password": make_hashes(new_p),
                            "first_name": f_name, "last_name": l_name,
                            "other_name": o_name if o_name else None,
                            "dob": str(dob), "email": email,
                            "phone_number": f"{phone_code} {phone_body}",
                            "must_reset": False
                        }
                        supabase.table("users").insert(user_insert).execute()
                        st.success("🎉 Account created! Log in to start.")
                    except Exception:
                        st.error("🚫 Username or Email already in use.")

# --- 6. MANDATORY RESET OVERLAY ---
elif st.session_state.must_reset:
    st.title("🔒 Change Your Password")
    st.warning("You must set a new permanent password to access your account.")
    
    _, center_reset, _ = st.columns([1, 2, 1])
    with center_reset:
        new_pass = st.text_input("New Password", type="password")
        conf_pass = st.text_input("Confirm Password", type="password")
        
        if st.button("Update and Continue", use_container_width=True):
            if new_pass == conf_pass and len(new_pass) >= 6:
                supabase.table("users").update({
                    "password": make_hashes(new_pass),
                    "must_reset": False
                }).eq("username", st.session_state.username).execute()
                st.session_state.must_reset = False
                st.success("Password updated successfully!")
                st.rerun()
            else:
                st.error("Passwords must match and be at least 6 characters.")

# --- 7. MAIN DASHBOARD ---
else:
    is_admin = (st.session_state.username == "admin")
    st.sidebar.title(f"👋 {st.session_state.username}")
    
    page = st.sidebar.radio("Navigation", ["My Portfolio", "Admin Panel"] if is_admin else ["My Portfolio"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if page == "Admin Panel" and is_admin:
        st.subheader("🛡️ Admin Panel")
        u_data = supabase.table("users").select("*").execute()
        u_df = pd.DataFrame(u_data.data)

        if not u_df.empty:
            for i, row in u_df.iterrows():
                with st.expander(f"👤 {row['first_name']} {row['last_name']} (@{row['username']})"):
                    st.write(f"**Email:** {row['email']} | **Phone:** {row['phone_number']}")
                    if row['username'] != "admin":
                        v = st.session_state.list_version
                        if st.button("🗑️ Delete", key=f"ad_del_{row['username']}_{v}", type="primary"):
                            handle_user_deletion(row['username'])
    else:
        st.write("### 📈 Portfolio Dashboard Active")
