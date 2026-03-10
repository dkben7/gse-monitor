import streamlit as st
import pandas as pd

# Page Config
st.set_page_config(page_title="GSE Portfolio Monitor", layout="wide")
st.title("🇬🇭 GSE Smart Monitor")

# REPLACE THIS ID with the long string of letters/numbers in your URL
SHEET_ID = "1_x73bJfJEJJGTZFsB1rzzM2oz0Yrxe5ViHQVvLhmEek"

# URLs for your specific tabs
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
    
    # --- CLEANING LOGIC ---
    # Using iloc to target the 3rd column safely for the Change
    p_df['clean_change'] = p_df.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    p_df['clean_change'] = pd.to_numeric(p_df['clean_change'], errors='coerce').fillna(0)
    
    return p_df, d_df

try:
    portfolio, dividends = get_data()

    # Metrics Row
    total_div_ghs = dividends['dividend received'].sum()
    st.metric("Total Dividends (GHS)", f"GH₵ {total_div_ghs:,.2f}")

    # Main Dashboard Columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🚀 Top Gainers")
        gainers = portfolio['clean_change'] > 0].nlargest(5, 'Clean_Change')
        st.dataframe(gainers[['Ticker', 'Clean_Change']], hide_index=True)

    with col2:
        st.subheader("📉 Top Losers")
        # Same "Absolute Value" logic: finds numbers that aren't positive or zero
        losers = portfolio['clean_change'] < 0].nsmallest(5, 'Clean_Change')
        st.dataframe(losers[['Ticker', 'Clean_Change']], hide_index=True)

    with col3:
        st.subheader("💰 Top Dividend Payers")
        # Grouping by Stock and summing, just like our QUERY
        top_divs = dividends.groupby('stock')['dividend received'].sum().nlargest(5).reset_index()
        st.dataframe(top_divs, hide_index=True)

except Exception as e:
    st.error("Could not connect to Google Sheets. Check your Sheet ID and Permissions.")
    st.write(e)
