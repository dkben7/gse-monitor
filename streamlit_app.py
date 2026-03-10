import streamlit as st
import pandas as pd

# 1. Professional Page Config
st.set_page_config(page_title="GSE Intelligence", page_icon="📈", layout="wide")

# Custom CSS for "Glass" Effect (Works in Dark and Light mode)
st.markdown("""
    <style>
    [data-testid="stMetric"] { 
        background-color: rgba(255, 255, 255, 0.05); 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    .stDataFrame { border-radius: 15px; overflow: hidden; }
    h2, h3 { letter-spacing: -1px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 GSE Smart Intelligence")

# --- SETTINGS (Keep your ID) ---
SHEET_ID = "1_x73bJfJEJJGTZFsB1rzzM2oz0Yrxe5ViHQVvLhmEek" 
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=60)
def get_data(sheet_name):
    url = f"{BASE_URL}&sheet={sheet_name}"
    return pd.read_csv(url)

try:
    portfolio = get_data("Portfolio")
    dividends = get_data("Dividends")
    
    portfolio.columns = portfolio.columns.str.lower().str.strip()
    dividends.columns = dividends.columns.str.lower().str.strip()

    # Cleaning Logic
    portfolio['clean_change'] = portfolio.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    portfolio['clean_change'] = pd.to_numeric(portfolio['clean_change'], errors='coerce').fillna(0)

    # --- TOP METRICS ROW ---
    m1, m2, m3 = st.columns(3)
    
    if 'dividend received' in dividends.columns:
        total_div = dividends['dividend received'].sum()
        m1.metric("Total Dividends", f"GH₵ {total_div:,.2f}")
    
    up_tickers = len(portfolio[portfolio['clean_change'] > 0])
    m2.metric("Market Sentiment", f"{up_tickers} Stocks UP", delta=f"{up_tickers/len(portfolio):.0%}")
    m3.metric("Status", "Live Feed", delta="Connected", delta_color="normal")

    st.write("---")

    # --- MAIN CONTENT ---
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚀 Top Performers")
        gainers = portfolio[portfolio['clean_change'] > 0].nlargest(5, 'clean_change')
        # Format the numbers to show decimals
        st.dataframe(
            gainers[['ticker', 'clean_change']], 
            column_config={
                "clean_change": st.column_config.NumberColumn("Change", format="%.2f")
            },
            hide_index=True, 
            use_container_width=True
        )

    with col2:
        st.subheader("📉 Top Losers")
        losers = portfolio[portfolio['clean_change'] < 0].nsmallest(5, 'clean_change')
        st.dataframe(
            losers[['ticker', 'clean_change']], 
            column_config={
                "clean_change": st.column_config.NumberColumn("Change", format="%.2f")
            },
            hide_index=True, 
            use_container_width=True
        )

    # --- BAR CHART ---
    st.write("---")
    st.subheader("💰 Dividend Income by Stock")
    if 'stock' in dividends.columns:
        top_divs = dividends.groupby('stock')['dividend received'].sum().sort_values(ascending=False).reset_index()
        st.bar_chart(data=top_divs, x='stock', y='dividend received', color="#00ff88")

except Exception as e:
    st.error(f"⚠️ App Error: {e}")
