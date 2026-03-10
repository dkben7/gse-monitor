import streamlit as st
import pandas as pd

# 1. Page Config & Professional Theme
st.set_page_config(page_title="GSE Intelligence Pro", page_icon="🏦", layout="wide")

# Custom Global CSS
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1); }
    .stDataFrame { border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State for Data Persistence
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'target_id' not in st.session_state:
    st.session_state.target_id = ""

# --- SIDEBAR AUTH & NAVIGATION ---
with st.sidebar:
    st.title("🏦 GSE Pro App")
    if not st.session_state.authenticated:
        pwd = st.text_input("App Password", type="password")
        if st.button("Login"):
            if pwd == "GSE2026":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid Password")
    
    if st.session_state.authenticated:
        st.success("Authenticated")
        st.session_state.target_id = st.text_input("Google Sheet ID", value=st.session_state.target_id)
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

# --- MULTI-PAGE ROUTING ---
if st.session_state.authenticated and st.session_state.target_id:
    # This automatically detects files in the 'pages/' folder
    st.info("Select a page from the sidebar to view your data.")
else:
    st.title("Welcome to GSE Intelligence Pro")
    st.write("Please log in and provide your Sheet ID in the sidebar to access your dynamic dashboard.")
