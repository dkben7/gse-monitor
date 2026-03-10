import streamlit as st
import pandas as pd
from supabase import create_client, Client
import hashlib
import datetime

# --- 1. DATABASE CONNECTION ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# --- 2. COUNTRY CODE DATA ---
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
st.set_page_config(page_title="GSE Intelligence", page_icon="🏦", layout="wide")
st.title("🏦 GSE Intelligence")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'list_version' not in st.session_state:
    st.session_state.list_version = 0

# --- 4. CALLBACK FUNCTIONS ---
def handle_user_deletion(username_to_del):
    """Deletes user data and triggers a clean rerun to reset widget states."""
    try:
        supabase.table("portfolio").delete().eq("username", username_to_del).execute()
        supabase.table("users").delete().eq("username", username_to_del).execute()
        st.session_state.list_version += 1
        st.toast(f"✅ User '{username_to_del}' and their data removed.")
    except Exception as e:
        st.error(f"⚠️ Error during deletion: {e}")
    st.rerun()

# --- 5. AUTHENTICATION INTERFACE ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        u = st.text_input("Username", key="login_u").lower().strip()
        p = st.text_input("Password", type="password", key="login_p")
        
        col_login, col_forgot = st.columns([1, 4])
        
        if col_login.button("Sign In"):
            res = supabase.table("users").select("*").eq("username", u).eq("password", make_hashes(p)).execute()
            if res.data:
                now = datetime.datetime.now().isoformat()
                supabase.table("users").update({"last_login": now}).eq("username", u).execute()
                st.session_state.logged_in = True
                st.session_state.username = u
                st.rerun()
            else:
                st.error("❌ Incorrect username or password.")
        
        with col_forgot.popover("Forgot Password?"):
            st.write("### Reset Password")
            st.info("For security, password resets are handled by the administrator.")
            reset_user = st.text_input("Username for Reset Request").lower().strip()
            if st.button("Submit Request"):
                if reset_user:
                    st.success(f"Request logged for {reset_user}. Contact Admin for verification.")
                else:
                    st.warning("Please provide a username.")

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
            # Default to Ghana (+233) or United States (+1) if preferred
            default_idx = sorted(COUNTRY_DATA.keys()).index("Ghana")
            selected_country = c_cc.selectbox("Country Code", code_options, index=default_idx)
            phone_body = c_ph.text_input("Phone Number")
            
            st.divider()
            st.write("### Account Credentials")
            new_u = st.text_input("New Username").lower().strip()
            new_p = st.text_input("New Password", type="password")
            
            if st.form_submit_button("Register"):
                # Other Name is the ONLY optional field
                required = [f_name, l_name, email, phone_body, new_u, new_p]
                if not all(required):
                    st.warning("All fields are required except 'Other Name'.")
                else:
                    try:
                        # Extract the code (e.g., +233) from the "Country (+Code)" string
                        phone_code = selected_country.split('(')[-1].strip(')')
                        full_phone = f"{phone_code} {phone_body}"
                        
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
                        st.success("🎉 Account created! You can now log in.")
                        st.balloons()
                    except Exception as e:
                        st.error("🚫 Registration failed. Username, Email, or Phone may already be registered.")

# --- 6. MAIN APPLICATION CONTENT ---
else:
    is_admin = (st.session_state.username == "admin")
    st.sidebar.title(f"👋 {st.session_state.username}")
    
    # Navigation
    menu = ["My Portfolio", "Admin Panel"] if is_admin else ["My Portfolio"]
    page = st.sidebar.radio("Navigation", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    # --- ADMIN PANEL ---
    if page == "Admin Panel" and is_admin:
        st.subheader("🛡️ Admin Control Panel")
        user_res = supabase.table("users").select("*").execute()
        user_df = pd.DataFrame(user_res.data)

        if not user_df.empty:
            st.write(f"Total Members: **{len(user_df)}**")
            for i, row in user_df.iterrows():
                # Build display name logic
                full_display = f"{row['first_name']} {row['last_name']}"
                if row.get('other_name'):
                    full_display = f"{row['first_name']} {row['other_name']} {row['last_name']}"
                
                with st.expander(f"👤 {full_display} (@{row['username']})"):
                    col_a, col_b = st.columns(2)
                    col_a.write(f"**Email:** {row['email']}")
                    col_a.write(f"**Phone:** {row['phone_number']}")
                    col_b.write(f"**DOB:** {row['dob']}")
                    
                    last_seen = pd.to_datetime(row['last_login']).strftime('%b %d, %Y at %H:%M') if row['last_login'] else "Never"
                    col_b.write(f"**Last Login:** {last_seen}")
                    
                    if row['username'] != "admin":
                        # Unique keys prevent "stale" open popovers
                        v = st.session_state.list_version
                        if st.button(f"🗑️ Delete User", key=f"del_{row['username']}_{v}", type="primary"):
                            handle_user_deletion(row['username'])
        else:
            st.info("No registered users yet.")

    # --- PORTFOLIO PAGE ---
    else:
        st.subheader("📈 My Portfolio")
        st.info("Portfolio management system active. Use the sidebar to navigate.")
        # [Insert your existing Portfolio Transaction & Table logic here]
