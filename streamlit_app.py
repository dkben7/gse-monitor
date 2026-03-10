import streamlit as st
import pandas as pd
import sqlite3
import hashlib

# 1. Database Setup for Users
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')
    conn.commit()
    conn.close()

def add_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    # Hash password for security
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute('INSERT INTO userstable(username, password) VALUES (?,?)', (username, hashed_pw))
    conn.commit()
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute('SELECT * FROM userstable WHERE username =? AND password = ?', (username, hashed_pw))
    data = c.fetchall()
    conn.close()
    return data

# 2. Page Config
st.set_page_config(page_title="GSE Pro Login", layout="centered")
init_db()

# 3. UI
st.title("🏦 GSE Intelligence Pro")
menu = ["Login", "SignUp"]
choice = st.selectbox("Menu", menu)

if choice == "Login":
    st.subheader("Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        result = login_user(username, password)
        if result:
            st.success(f"Logged In as {username.capitalize()}")
            st.session_state['logged_in'] = True
            st.session_state['username'] = username
            st.info("Now, enter your Google Sheet ID in the sidebar to start.")
            # This is where the navigation will appear
        else:
            st.error("Incorrect Username/Password")

elif choice == "SignUp":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')
    
    if st.button("Signup"):
        add_user(new_user, new_password)
        st.success("Account created successfully!")
        st.info("Go to Login Menu to sign in.")

# --- DYNAMIC SIDEBAR (Only shows if logged in) ---
if st.session_state.get('logged_in'):
    with st.sidebar:
        st.write(f"Welcome, **{st.session_state['username'].capitalize()}**")
        st.session_state['sheet_id'] = st.text_input("Your Google Sheet ID")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # IF LOGGED IN AND ID PROVIDED, SHOW THE APP CONTENT
    if st.session_state.get('sheet_id'):
        st.divider()
        st.write("### Choose a Module")
        # Instead of pages/ folder, we can use buttons for a "Standard" App feel
        if st.button("View Executive Dashboard"):
             st.info("Redirecting to Dashboard...") # In next step we integrate logic here
