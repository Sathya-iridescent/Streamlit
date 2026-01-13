"""
Authentication helper functions
"""
from flask import session
from database import get_db_session
from models.user import User


def get_current_user():
    """
    Get the currently logged-in user from session.
    Returns User object or None if not logged in.
    The user object is expunged from the session so it can be used after the session closes.
    """
    if 'user_id' not in session:
        return None
    
    try:
        with get_db_session() as db_session:
            user = db_session.query(User).filter_by(id=session['user_id']).first()
            if user and user.is_active:
                # Pre-load all attributes while session is open
                _ = user.username
                _ = user.email
                _ = user.full_name
                _ = user.phone
                _ = user.company
                _ = user.role
                _ = user.created_at
                _ = user.last_login
                _ = user.is_active
                _ = user.is_verified
                
                # Expunge the object so it can be used after session closes
                db_session.expunge(user)
                return user
            else:
                # User not found or inactive, clear session
                session.clear()
                return None
    except Exception:
        return None


def login_user(user):
    """
    Log in a user by setting session variables.
    """
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session.permanent = True  # Session persists across browser restarts
    session.modified = True  # Mark session as modified to extend timeout


def logout_user():
    """
    Log out the current user by clearing session.
    """
    session.clear()

