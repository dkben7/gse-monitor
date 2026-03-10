import streamlit as st
import pandas as pd

# 1. Professional Page Config
st.set_page_config(page_title="GSE Intelligence", page_icon="📈", layout="wide")

# Custom CSS Fix (Fixed the unsafe_index error)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    [data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 15px; border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 GSE Smart Intelligence")

# --- IMPORTANT: PASTE YOUR ACTUAL ID HERE ---
SHEET_ID = "1_x73bJfJEJJGTZFsB1rzzM2oz0Yrxe5ViHQVvLhmEek" 

# Base URL for the sheet
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=60)
def get_data(sheet_name):
    url = f"{BASE_URL}&sheet={sheet_name}"
    return pd.read_csv(url)

try:
    # Attempt to load tabs
    portfolio = get_data("Portfolio")
    dividends = get_data("Dividends")
    
    # Standardize column names
    portfolio.columns = portfolio.columns.str.lower().str.strip()
    dividends.columns = dividends.columns.str.lower().str.strip()

    # Cleaning Logic for Daily Change (Assuming it's the 3rd column)
    portfolio['clean_change'] = portfolio.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    portfolio['clean_change'] = pd.to_numeric(portfolio['clean_change'], errors='coerce').fillna(0)

    # --- TOP METRICS ---
    m1, m2, m3 = st.columns(3)
    
    if 'dividend received' in dividends.columns:
        total_div = dividends['dividend received'].sum()
        m1.metric("Total Dividends Earned", f"GH₵ {total_div:,.2f}")
    
    up_tickers = len(portfolio[portfolio['clean_change'] > 0])
    m2.metric("Market Sentiment", f"{up_tickers} Stocks UP")
    m3.metric("Status", "Live", delta="Connected")

    st.divider()

    # --- DASHBOARD TABLES ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚀 Top Performers")
        gainers = portfolio[portfolio['clean_change'] > 0].nlargest(5, 'clean_change')
        st.dataframe(gainers[['ticker', 'clean_change']], hide_index=True, use_container_width=True)

    with col2:
        st.subheader("📉 Top Losers")
        losers = portfolio[portfolio['clean_change'] < 0].nsmallest(5, 'clean_change')
        st.dataframe(losers[['ticker', 'clean_change']], hide_index=True, use_container_width=True)

    # --- BAR CHART ---
    st.subheader("💰 Dividend Leaderboard")
    if 'stock' in dividends.columns:
        top_divs = dividends.groupby('stock')['dividend received'].sum().nlargest(8).reset_index()
        st.bar_chart(data=top_divs, x='stock', y='dividend received', color="#2ecc71")

except Exception as e:
    st.error("⚠️ Connection Issue Detected")
    st.info("Check these 3 things:")
    st.write("1. Is your Sheet ID correct?")
    st.write(f"2. Are your tabs named exactly **Portfolio** and **Dividends**? (Case sensitive)")
    st.write("3. Is the Google Sheet shared as 'Anyone with the link can view'?")
    st.write(f"**Technical Error:** {e}")
