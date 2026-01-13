import streamlit as st
from datetime import datetime
from database import get_db_session
from models.user import User

def login_user_logic(username_or_email, password):
    """The Streamlit version of your login route"""
    try:
        with get_db_session() as db_session:
            # Look for user
            user = db_session.query(User).filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    st.error("Your account is deactivated")
                    return False
                
                # Update last login
                user.last_login = datetime.utcnow()
                db_session.commit()
                
                # Save to Streamlit Session State (instead of Flask Session)
                st.session_state.authenticated = True
                st.session_state.user_id = user.id
                st.session_state.username = user.username
                st.session_state.role = user.role
                return True
            else:
                st.error("Invalid username/email or password")
                return False
    except Exception as e:
        st.error(f"Database error: {e}")
        return False

def logout():
    """Clear session and rerun"""
    for key in list(st.session_state.keys()):
        delete st.session_state[key]
    st.rerun()