import streamlit as st
import pandas as pd

# This page inherits the login status from the main app
if 'authenticated' in st.session_state and st.session_state.authenticated:
    st.title("💰 Dividend Cashflow Analysis")
    
    # 1. Load and Clean Dividend Data
    base_url = f"https://docs.google.com/spreadsheets/d/{st.session_state.target_id}/gviz/tq?tqx=out:csv&sheet=Dividends"
    df = pd.read_csv(base_url)
    
    # Global Capitalization
    df.columns = [col.strip().title() for col in df.columns]
    df['Stock'] = df['Stock'].astype(str).str.title()
    
    # 2. Key Metric
    total = df['Dividend Received'].sum()
    st.metric("Total Life-Time Dividends", f"GH₵ {total:,.2f}")
    
    # 3. Income Chart
    st.subheader("Income by Ticker")
    chart_data = df.groupby('Stock')['Dividend Received'].sum().sort_values(ascending=False).reset_index()
    st.bar_chart(data=chart_data, x='Stock', y='Dividend Received', color="#00ff88")
    
    # 4. Raw Data Table
    with st.expander("View Full Transaction History"):
        st.dataframe(df, hide_index=True)
else:
    st.warning("Please login on the Home page first.")
