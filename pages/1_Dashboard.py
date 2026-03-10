import streamlit as st
import pandas as pd

def get_clean_data():
    base_url = f"https://docs.google.com/spreadsheets/d/{st.session_state.target_id}/gviz/tq?tqx=out:csv"
    p_df = pd.read_csv(f"{base_url}&sheet=Portfolio")
    
    # --- GLOBAL CAPITALIZATION & CLEANING ---
    # 1. Capitalize Column Headers
    p_df.columns = [col.strip().title() for col in p_df.columns]
    
    # 2. Capitalize Row Data (Tickers)
    p_df.iloc[:, 0] = p_df.iloc[:, 0].astype(str).str.title()
    
    # 3. Handle Brackets & Zeros
    p_df['Clean_Change'] = p_df.iloc[:, 2].astype(str).str.replace('(', '-', regex=False).str.replace(')', '', regex=False)
    p_df['Clean_Change'] = pd.to_numeric(p_df['Clean_Change'], errors='coerce').fillna(0)
    
    # --- KILL THE GHOST ZEROS ---
    # Filter out anything where Change is 0 OR Ticker is empty/zero
    p_df = p_df[p_df['Clean_Change'] != 0]
    p_df = p_df[p_df.iloc[:, 0].str.len() > 1]
    
    return p_df

if st.session_state.authenticated and st.session_state.target_id:
    df = get_clean_data()
    st.header("🚀 Executive Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Performers")
        gainers = df[df['Clean_Change'] > 0].nlargest(5, 'Clean_Change')
        st.dataframe(gainers.iloc[:, [0, -1]], hide_index=True, use_container_width=True)
        
    with col2:
        st.subheader("Top Losers")
        losers = df[df['Clean_Change'] < 0].nsmallest(5, 'Clean_Change')
        st.dataframe(losers.iloc[:, [0, -1]], hide_index=True, use_container_width=True)
