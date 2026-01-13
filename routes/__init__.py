"""
Routes package - All route handlers
"""
from .auth_routes import auth_bp
from .po_routes import po_bp
from .dashboard_routes import dashboard_bp
from .style_master_routes import style_master_bp

__all__ = ['auth_bp', 'po_bp', 'dashboard_bp', 'style_master_bp']


