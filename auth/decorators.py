"""
Authentication decorators - Route protection
"""
from functools import wraps
from flask import session, redirect, url_for, request
from .helpers import get_current_user


def login_required(f):
    """
    Decorator to protect routes that require authentication.
    Redirects to login page if user is not logged in.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Store the URL the user was trying to access
            if request.endpoint and request.endpoint != 'login':
                session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorator to protect routes that require admin role.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            from flask import flash
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        
        user = get_current_user()
        if not user or user.role != 'admin':
            from flask import flash
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

