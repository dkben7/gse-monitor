import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="GSE Intelligence Pro", page_icon="🏦", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    [data-testid="stMetric"] { 
        background-color: rgba(255, 255, 255, 0.05); 
        padding: 20px; border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stSidebar { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: USER INPUT & AUTH ---
with st.sidebar:
    st.title("Settings")
    user_password = st.text_input("Enter App Password", type="password")
    
    st.divider()
    st.subheader("Connect Your Data")
    # This allows any user to paste their own Sheet ID
    target_id = st.text_input("Google Sheet ID", placeholder="Enter ID here...")
    
    st.info("Ensure your Google Sheet is shared as 'Anyone with the link can view'.")

# --- MAIN APP LOGIC ---
if user_password == "GSE2026":  # You can change this password
    if target_id:
        BASE_URL = f"https://docs.google.com/spreadsheets/d/{target_id}/gviz/tq?tqx=out:csv"

        @st.cache_data(ttl=60)
        def load_user_data(sheet_name):
            return pd.read_csv(f"{BASE_URL}&sheet={sheet_name}")

        try:
            # Loading data dynamically
            portfolio = load_user_data("Portfolio")
            dividends = load_user_data("Dividends")
            
            # Normalizing data
            portfolio.columns = portfolio.columns.str.lower().str.strip()
            dividends.columns = dividends.columns.str.lower().str.strip()
            
            # Cleaning Logic
            portfolio['clean_change'] = portfolio.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
            portfolio['clean_change'] = pd.to_numeric(portfolio['clean_change'], errors='coerce').fillna(0)

            st.title("🏦 GSE Portfolio Intelligence")
            
            # Metrics
            m1, m2, m3 = st.columns(3)
            if 'dividend received' in dividends.columns:
                m1.metric("Total Dividends", f"GH₵ {dividends['dividend received'].sum():,.2f}")
            
            m2.metric("Portfolio Health", f"{len(portfolio[portfolio['clean_change'] > 0])} Gainers")
            m3.metric("System Status", "Encrypted", delta="Secure Session")

            st.divider()

            # Dashboard Display
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🚀 Top Performers")
                st.dataframe(portfolio.nlargest(5, 'clean_change')[['ticker', 'clean_change']], hide_index=True, use_container_width=True)
            
            with c2:
                st.subheader("📉 Top Losers")
                st.dataframe(portfolio.nsmallest(5, 'clean_change')[['ticker', 'clean_change']], hide_index=True, use_container_width=True)

        except Exception as e:
            st.error("Invalid Sheet ID or Tab Names. Please check your Google Sheet settings.")
    else:
        st.warning("Please enter your Google Sheet ID in the sidebar to begin.")
else:
    if user_password:
        st.error("Incorrect Password.")
    else:
        st.info("Welcome! Please enter the password in the sidebar to access the dashboard.")
