"""
Style Master Routes - Manage EAN to Style/Buyer mappings
"""
from flask import Blueprint, render_template, request, redirect
from database import get_db_session
from models.style_master import StyleMaster
from auth.decorators import login_required

style_master_bp = Blueprint('style_master', __name__)

# Import constants from config
from config import BUYERS


@style_master_bp.route("/style-master")
@login_required
def style_master():
    """Style master management page"""
    with get_db_session() as session:
        # Query style_master table (id is primary key, ean is unique)
        styles = session.query(StyleMaster).order_by(StyleMaster.id.desc()).all()
        rows = [style.to_dict() for style in styles]
    return render_template("style_master.html", styles=rows, buyers=BUYERS)


@style_master_bp.route("/save_style", methods=["POST"])
@login_required
def save_style():
    """Save or update style master entry"""
    ean = request.form.get("ean", "").strip()
    style = request.form.get("style_no", "").strip()
    buyer = request.form.get("buyer", "").strip()

    if not ean:
        return redirect("/style-master")

    with get_db_session() as session:
        # If same EAN exists, update it; else insert new
        style_master = session.query(StyleMaster).filter_by(ean=ean).first()
        if style_master:
            style_master.style_no = style
            style_master.buyer = buyer
        else:
            style_master = StyleMaster(ean=ean, style_no=style, buyer=buyer)
            session.add(style_master)
        # commit happens automatically via context manager
    
    return redirect("/style-master")


@style_master_bp.route("/delete_style/<int:id>")
@login_required
def delete_style(id):
    """Delete style_master by id"""
    with get_db_session() as session:
        style_master = session.query(StyleMaster).filter_by(id=id).first()
        if style_master:
            session.delete(style_master)
        # commit happens automatically via context manager
    return redirect("/style-master")


@style_master_bp.route("/refresh_styles")
@login_required
def refresh_styles():
    """Refresh style_no and buyer in po_items from style_master using JOIN"""
    from models.po_item import POItem
    
    with get_db_session() as session:
        # Use JOIN to update po_items with style_master data
        po_items = session.query(POItem).all()
        for po_item in po_items:
            if po_item.ean:
                # Get style_master via relationship or direct query
                style_master = session.query(StyleMaster).filter_by(ean=po_item.ean).first()
                if style_master:
                    po_item.style_no = style_master.style_no or ""
                    po_item.buyer = style_master.buyer or ""
        # commit happens automatically via context manager
    
    return redirect("/dashboard")

