import streamlit as st
import os
from datetime import datetime
# Keep your existing imports
from database import initialize_db, get_db_session, SessionLocal
from models import User, POItem, StyleMaster
from config import FACTORIES, TRANSPORTERS, BUYERS


# 1. Initialize Database (Same as your Flask app)
initialize_db()


# 2. Setup Session State for Security
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def logout():
    st.session_state.authenticated = False
    st.session_state.clear()
    st.rerun()

# --- UI CONTROL FLOW ---

if not st.session_state.authenticated:
    st.title("📦 DMart Dashboard")
    
    # Create the form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
    if submit:
        # Use your get_db_session helper from database.py
        with get_db_session() as session:
            user = session.query(User).filter_by(username=username).first()
            
            # Check password hash using the method in your User model
            if user and user.check_password(password):
                # SET ALL STATE BEFORE RERUNNING
                st.session_state.authenticated = True
                st.session_state.username = user.username
                st.session_state.role = user.role
                st.session_state.user_id = user.id
                
                # IMPORTANT: Set a default location for your calculations later
                # We will use this for the -6, -4, -3 day rules
                st.session_state.location = user.company if user.company else "Unknown"
                
                st.success("Login Successful! Redirecting...")
                st.rerun() # This will now trigger the 'else' block below
            else:
                st.error("Invalid credentials")
else:
    # --- LOGGED IN AREA ---
    st.sidebar.title(f"User: {st.session_state.username}")
    st.sidebar.info(f"Role: {st.session_state.role}")
    
    # Navigation Menu (Replaces your Flask Blueprints/Routes)
    menu = ["Dashboard", "Ex-Factory Calculator", "Style Master", "PO List"]
    choice = st.sidebar.radio("Main Menu", menu)
    
    if st.sidebar.button("Logout"):
        logout()

    # --- PAGE LOGIC ---
    if choice == "Dashboard":
        st.header("Operations Dashboard")
        st.write("Overview of pending POs and recent updates.")
        # Add charts or summary metrics here
        
    elif choice == "Ex-Factory Calculator":
        st.header("Date Calculation Tool")
        # I'll help you build the date logic here next using your rules!
        delivery_date = st.date_input("Select Delivery Date")
        location = st.selectbox("Select Location", FACTORIES)
        
        # Here we will apply your: Vadodara -6, Bhiwandi -4 etc. rules
        st.info("Calculation logic will show here.")

    elif choice == "Style Master":
        st.header("Style Master Management")
        # Logic to view/add styles from your StyleMaster model













