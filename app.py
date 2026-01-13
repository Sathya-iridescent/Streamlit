"""
PO Extract Application - Main Flask App
Modular structure with authentication and route protection
"""
from flask import Flask, jsonify, render_template
import os
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict

# Load environment variables
load_dotenv()

# Import database initialization
from database import initialize_db, get_db_session

# Import models (to ensure they're registered with Base)
from models import User, POItem, StyleMaster

# Import blueprints
from routes.auth_routes import auth_bp
from routes.po_routes import po_bp
from routes.dashboard_routes import dashboard_bp
from routes.style_master_routes import style_master_bp

# Initialize Flask app
app = Flask(__name__)

# Secret key for sessions (required for authentication)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-please')

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('SESSION_TIMEOUT', 3600))  # Default 1 hour (3600 seconds)
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Make session timeout available to templates
@app.context_processor
def inject_session_timeout():
    return dict(session_timeout=app.config['PERMANENT_SESSION_LIFETIME'])

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(po_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(style_master_bp)

# Import constants from config
from config import FACTORIES, TRANSPORTERS, BUYERS

# Make constants available to templates
app.jinja_env.globals['FACTORIES'] = FACTORIES
app.jinja_env.globals['TRANSPORTERS'] = TRANSPORTERS
app.jinja_env.globals['BUYERS'] = BUYERS

# Initialize database (creates tables if they don't exist)
initialize_db()
   
# ---------------- HEALTH CHECK ROUTE ---------------- #


@app.route("/health")
def health_check():
    """
    Health check endpoint for Render.com monitoring.
    Returns 200 OK if the service is running and database is accessible.
    """
    try:
        # Quick database connectivity check
        with get_db_session() as session:
            # Simple query to verify database connection
            session.query(POItem).limit(1).all()
        
        return jsonify({
            "status": "healthy",
            "service": "PO Extract",
            "timestamp": datetime.now().isoformat()
        }), 200
    except Exception as e:
        # If database check fails, still return 200 but with warning
        # This prevents Render from marking service as down due to DB issues
        return jsonify({
            "status": "degraded",
            "service": "PO Extract",
            "timestamp": datetime.now().isoformat(),
            "warning": "Database connectivity issue"
        }), 200


@app.route("/")
def index():
    """Root route - redirect to login or dashboard based on auth status"""
    from flask import redirect, url_for, session
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('auth.login'))



# ---------------- ENTRY POINT ---------------- #

if __name__ == '__main__':	
    # Development mode: Use Flask dev server with auto-reload
    # Production mode: Use Waitress server (for Render.com)
    dev_mode = os.environ.get('FLASK_ENV', 'development').lower() == 'development'
    
    if dev_mode:
        # Development: Flask dev server with debug mode
        port = int(os.environ.get('PORT', 5001))
        debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
        print(f"🚀 Starting Flask development server on http://0.0.0.0:{port}")
        print(f"   Debug mode: {debug}")
        app.run(host='0.0.0.0', port=port, debug=debug)
    else:
        # Production: Waitress server (for Render.com)
        from waitress import serve
        port = int(os.environ.get('PORT', 10000))
        print(f"🚀 Starting Waitress production server on http://0.0.0.0:{port}")
        serve(app, host='0.0.0.0', port=port)
if __name__ == '__main__':
    print("🔥 FORCE DEBUG MODE 🔥")
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
