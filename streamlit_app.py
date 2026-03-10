import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="GSE Portfolio Monitor", layout="wide")
st.title("🇬🇭 GSE Smart Monitor")

# --- SETTINGS ---
# Replace this with your actual Sheet ID
SHEET_ID = "1_70V_S-N_D-W_K_O_E_X_A_M_P_L_E" 

PORTFOLIO_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Portfolio"
DIVIDENDS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Dividends"

@st.cache_data(ttl=300)
def get_data():
    # Load Data
    p_df = pd.read_csv(PORTFOLIO_URL)
    d_df = pd.read_csv(DIVIDENDS_URL)
    
    # Standardize column names (lowercase and strip spaces)
    p_df.columns = p_df.columns.str.lower().str.strip()
    d_df.columns = d_df.columns.str.lower().str.strip()
    
    # CLEANING LOGIC: Fix the brackets in the 3rd column (Index 2)
    p_df['clean_change'] = p_df.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    p_df['clean_change'] = pd.to_numeric(p_df['clean_change'], errors='coerce').fillna(0)
    
    return p_df, d_df

try:
    portfolio, dividends = get_data()

    # 1. Metrics Row (Total Dividends)
    # Checks for 'dividend received' in lowercase
    if 'dividend received' in dividends.columns:
        total_div_ghs = dividends['dividend received'].sum()
        st.metric("Total Dividends (GHS)", f"GH₵ {total_div_ghs:,.2f}")
    else:
        st.warning("Column 'dividend received' not found in Dividends sheet.")

    # 2. Main Dashboard Columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🚀 Top Gainers")
        # Fixed the bracket syntax here
        gainers = portfolio[portfolio['clean_change'] > 0].nlargest(5, 'clean_change')
        st.dataframe(gainers[['ticker', 'clean_change']], hide_index=True)

    with col2:
        st.subheader("📉 Top Losers")
        # Logic: Find numbers less than 0
        losers = portfolio[portfolio['clean_change'] < 0].nsmallest(5, 'clean_change')
        st.dataframe(losers[['ticker', 'clean_change']], hide_index=True)

    with col3:
        st.subheader("💰 Top Dividend Payers")
        if 'stock' in dividends.columns and 'dividend received' in dividends.columns:
            top_divs = dividends.groupby('stock')['dividend received'].sum().nlargest(5).reset_index()
            st.dataframe(top_divs, hide_index=True)

except Exception as e:
    st.error("Connection Error. Check your Sheet ID and Permissions.")
    st.write(f"Details: {e}")
