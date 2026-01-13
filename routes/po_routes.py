"""
PO Routes - Upload and manage Purchase Orders
"""
from flask import Blueprint, render_template, request, jsonify, redirect, Response, url_for
import os
import fitz
import pandas as pd
import io
from datetime import datetime
from database import get_db_session
from models.po_item import POItem
from models.style_master import StyleMaster
from auth.decorators import login_required, admin_required
from extractor import extract_items
from utils.helpers import (
    calc_delivery_minus_4,
    calc_delivery_month,
    calc_no_of_boxes,
    calc_ex_factory
)

po_bp = Blueprint('po', __name__)

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def get_style_and_buyer_from_db(ean: str):
    """
    Returns (style_no, buyer) from style_master for a given EAN.
    If not found, returns ("", "").
    """
    with get_db_session() as session:
        style_master = session.query(StyleMaster).filter_by(ean=ean).first()
        if style_master:
            return (style_master.style_no or "", style_master.buyer or "")
    return "", ""


def ensure_ean_in_style_master(session, ean):
    """
    Ensure EAN exists in style_master table.
    If EAN is invalid (N/A, empty) -> returns None
    If EAN doesn't exist -> creates placeholder entry
    Returns validated EAN or None
    """
    if not ean or ean.strip() == "" or ean.upper() == "N/A":
        return None  # Set to NULL (foreign key allows NULL)
    
    ean = ean.strip()
    
    # Check if EAN exists in style_master
    style_master = session.query(StyleMaster).filter_by(ean=ean).first()
    
    if not style_master:
        # Create placeholder entry in style_master to satisfy foreign key
        placeholder = StyleMaster(
            ean=ean,
            style_no=None,
            buyer=None
        )
        session.add(placeholder)
        session.flush()  # Flush to get the ID, but don't commit yet
    
    return ean

def upsert_po_item(session, row):
    """
    Revised logic: 
    - If PO exists: Mark as 'is_amended' (Orange) and DO NOT overwrite data.
    - If PO is new: Create fresh row.
    """
    original_ean = row.get("ean", "")
    validated_ean = ensure_ean_in_style_master(session, original_ean)
    row["ean"] = validated_ean
    
    query_ean = validated_ean if validated_ean else None
    
    existing = session.query(POItem).filter_by(
        po_number=row["po_number"],
        ean=query_ean
    ).first()
    
    if not existing:
        # BRAND NEW PO: Create normally
        po_item = POItem(**row)
        session.add(po_item)
        return "new"

    else:

        # DUPLICATE FOUND: Turn Orange and unlock
        existing.is_amended = True
        # Check if values changed
        changed = False
        if existing.quantity != row.get("quantity", 0):
            changed = True
            existing.quantity = row["quantity"]
        if existing.delivery_date != row.get("delivery_date", ""):
            changed = True
            existing.delivery_date = row["delivery_date"]
        if existing.ex_factory_date != row.get("ex_factory_date", ""):
            changed = True
            existing.ex_factory_date = row["ex_factory_date"]
        
        if changed:
            new_balance = row.get("quantity", 0) - existing.dispatched_qty
            existing.balance = new_balance
            existing.is_revised = True
        return "duplicate"

@po_bp.route("/")
@login_required
def home():
    """Home page - redirects to upload"""
    return render_template("upload.html")


@po_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():
    """Upload PDF files for processing"""
    if request.method == "POST":
        files = request.files.getlist("pdf_files")
        extracted_data = []

        with get_db_session() as session:
            for pdf in files:
                if not pdf.filename:
                    continue

                filepath = os.path.join(UPLOAD_FOLDER, pdf.filename)
                pdf.save(filepath)

                with fitz.open(filepath) as doc:
                    text = "".join(page.get_text("text") for page in doc)

                rows = extract_items(text, pdf.filename)
                extracted_data.extend(rows)

                for r in rows:
                    # Extracted from PDF via extractor
                    original_delv = r["Delivery Date"]
                    po_no = r["PO #"]
                    po_date = r["PO Date"]
                    loc = r["Location"]
                    ean = r["EAN NO"]
                    desc = r["Article Description"]
                    caselot_raw = r["CaseLot"]
                    qty_raw = r["Quantity"]
                    fname = r["Filename"]

                    # Delivery date -4 days (as per your logic)
                    delv_adjusted = calc_delivery_minus_4(original_delv)

                    # Convert int
                    try:
                        caselot_int = int(caselot_raw)
                    except Exception:
                        caselot_int = 0

                    try:
                        qty_int = int(qty_raw)
                    except Exception:
                        qty_int = 0

                    # Derived fields - Get from style_master
                    style_no, buyer = get_style_and_buyer_from_db(ean)
                    delv_month = calc_delivery_month(delv_adjusted)
                    no_boxes = calc_no_of_boxes(caselot_int, qty_int)
                    ex_fty = calc_ex_factory(loc, delv_adjusted)
                    balance = qty_int

                    row = {
                        "filename": fname,
                        "po_number": po_no,
                        "po_date": po_date,
                        "style_no": style_no,
                        "ocn": "",
                        "buyer": buyer,
                        "delivery_date": delv_adjusted,
                        "delivery_month": delv_month,
                        "location": loc,
                        "ean": ean,
                        "description": desc,
                        "caselot": caselot_int,
                        "quantity": qty_int,
                        "no_of_boxes": no_boxes,
                        "factory": "",
                        "ex_factory_date": ex_fty,
                        "factory_remarks": "",
                        "dispatched_box": 0,
                        "dispatched_qty": 0,
                        "balance": balance,
                        "status": "Pending",
                        "dispatch_date": "",
                        "transporter": "",
                        "grn_date": "",
                        "grn_status": "",
                    }

                # 1. Use the correct variable name 'row' (not row_data)
                status = upsert_po_item(session, row)
                
                # 2. Check for duplicate to show the message
                if status == "duplicate":
                    from flask import flash
                    flash(f"PO {po_no} already exists! It has been highlighted Orange for manual revision.", "warning")

            # 3. Commit only ONCE after the loops finish
            session.commit()

        return render_template("results.html", data=extracted_data)

    return render_template("upload.html")


@po_bp.route("/download_excel")
@login_required
def download_excel():
    """Download dashboard data as Excel file"""
    from database import engine
    
    query = """
    SELECT 
        po_number, po_date, style_no, ocn, buyer, description,
        delivery_date, delivery_month, location, ean,
        caselot, quantity, no_of_boxes, factory, ex_factory_date,
        factory_remarks, dispatched_box, dispatched_qty, balance,
        status, dispatch_date, transporter, grn_date, grn_status,
        is_revised, created_at
    FROM po_items
    ORDER BY id DESC
    """
    
    df = pd.read_sql(query, engine)
    date_str = datetime.now().strftime("%Y%m%d")
    filename = f"PO_Dashboard_Export_{date_str}.xlsx"
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PO Items')
    
    output.seek(0)
    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# routes/po_routes.py

@po_bp.route("/admin/clear-po", methods=["POST"])
@admin_required
def clear_po_data():
    from models.po_item import POItem
    from database import get_db_session

    with get_db_session() as session:
        session.query(POItem).delete()
        session.commit()

    return redirect(url_for("dashboard.dashboard"))
@po_bp.route('/add-manual-row/<int:row_id>', methods=['POST'])
@login_required
def add_manual_row(row_id):
    with get_db_session() as session:
        parent = session.query(POItem).filter_by(id=row_id).first()
        if not parent:
            return jsonify({"ok": False, "error": "Parent not found"}), 404

        # Find next child sequence
        last_child = session.query(POItem)\
            .filter_by(parent_id=parent.id)\
            .order_by(POItem.child_seq.desc())\
            .first()

        next_seq = (last_child.child_seq + 1) if last_child else 1

        new_row = POItem(


            parent_id=parent.id,
            child_seq=next_seq,          # ✅ CRITICAL
            is_manual=True,
            ocn="",
            po_number=parent.po_number,
            style_no=parent.style_no,
            buyer=parent.buyer,
            description=parent.description,
            ean=parent.ean,
            location=parent.location,
            delivery_date=parent.delivery_date,
            delivery_month=parent.delivery_month,
            ex_factory_date=parent.ex_factory_date,
            caselot=parent.caselot,
            # --- ADD THESE 3 LINES HERE --
            factory="",            
            factory_remarks="",    
            dispatch_date="",      
            # -----------------
            quantity=0,
            dispatched_box=0,
            dispatched_qty=0,
            balance=0,
            status="Pending"
        )

        session.add(new_row)
        session.commit()

        return jsonify({"ok": True})
