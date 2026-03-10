import streamlit as st
import pandas as pd

# 1. Professional Page Config
st.set_page_config(page_title="GSE Intelligence", page_icon="📈", layout="wide")

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    [data-testid="stMetric"] { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        border: 1px solid #eee;
    }
    div[data-testid="stExpander"] { border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 GSE Smart Intelligence")
st.caption("Real-time Portfolio Analysis & Dividend Tracking")

# --- SETTINGS (Keep your existing ID) ---
SHEET_ID = "YOUR_SHEET_ID_HERE" 
PORTFOLIO_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Portfolio"
DIVIDENDS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Dividends"

@st.cache_data(ttl=300)
def get_data():
    p_df = pd.read_csv(PORTFOLIO_URL)
    d_df = pd.read_csv(DIVIDENDS_URL)
    p_df.columns = p_df.columns.str.lower().str.strip()
    d_df.columns = d_df.columns.str.lower().str.strip()
    
    # Cleaning Logic
    p_df['clean_change'] = p_df.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    p_df['clean_change'] = pd.to_numeric(p_df['clean_change'], errors='coerce').fillna(0)
    return p_df, d_df

try:
    portfolio, dividends = get_data()

    # --- TOP METRICS ROW ---
    m1, m2, m3 = st.columns(3)
    
    if 'dividend received' in dividends.columns:
        total_div = dividends['dividend received'].sum()
        m1.metric("Total Dividends Earned", f"GH₵ {total_div:,.2f}", delta="Annual Total")
    
    # Calculate Portfolio Health
    up_tickers = len(portfolio[portfolio['clean_change'] > 0])
    m2.metric("Market Sentiment", f"{up_tickers} Stocks UP", delta=f"{len(portfolio)} Total Watchlist")
    
    m3.metric("Status", "Operational", delta="Live Connection", delta_color="normal")

    st.divider()

    # --- MAIN CONTENT ---
    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.subheader("🚀 Top Performers")
            gainers = portfolio[portfolio['clean_change'] > 0].nlargest(5, 'clean_change')
            # Using column_config to add mini progress bars or colors
            st.dataframe(
                gainers[['ticker', 'clean_change']],
                column_config={
                    "ticker": "Stock Ticker",
                    "clean_change": st.column_config.NumberColumn("Daily Change", format="+%.2f")
                },
                hide_index=True,
                use_container_width=True
            )

    with col2:
        with st.container(border=True):
            st.subheader("📉 Top Losers")
            losers = portfolio[portfolio['clean_change'] < 0].nsmallest(5, 'clean_change')
            st.dataframe(
                losers[['ticker', 'clean_change']],
                column_config={
                    "ticker": "Stock Ticker",
                    "clean_change": st.column_config.NumberColumn("Daily Change", format="%.2f")
                },
                hide_index=True,
                use_container_width=True
            )

    # --- DIVIDEND SECTION ---
    st.subheader("💰 Dividend Cashflow Leaderboard")
    if 'stock' in dividends.columns:
        top_divs = dividends.groupby('stock')['dividend received'].sum().nlargest(8).reset_index()
        st.bar_chart(data=top_divs, x='stock', y='dividend received', color="#2ecc71")

except Exception as e:
    st.error("Authentication Error. Check Sheet Permissions.")
    st.write(f"Tech Details: {e}")
