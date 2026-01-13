"""
Dashboard Routes - Main dashboard view
"""
from datetime import datetime
from collections import defaultdict
from flask import Blueprint, render_template, url_for, redirect, request, jsonify
from sqlalchemy import case, func, or_
from database import get_db_session
from models.po_item import POItem
from models.style_master import StyleMaster
from auth.decorators import login_required
from auth.helpers import get_current_user 
from utils.helpers import calculate_exfactory_flag, parse_exfactory_date_for_sort, calc_delivery_month, calc_ex_factory, calc_no_of_boxes
from config import FACTORIES, TRANSPORTERS

dashboard_bp = Blueprint('dashboard', __name__)
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Main dashboard - shows all PO items with style and buyer info
    Requires authentication
    """
    with get_db_session() as session:
        # JOIN query to get PO items with style master data
        query = session.query(POItem, StyleMaster).outerjoin(
            StyleMaster, POItem.ean == StyleMaster.ean
        ).order_by(POItem.id.desc())
        
        results = query.all()
        
        processed = []
        for po_item, style_master in results:
            d = po_item.to_dict()

           # Clean up 'None' strings from DB
            for key in ['delivery_date', 'grn_date', 'po_date']:
                if d.get(key) == "None" or d.get(key) == None:
                    d[key] = ""
            
            # Override with style_master data if available
            if style_master:
                d['style_no'] = style_master.style_no or d.get('style_no', '')
                d['buyer'] = style_master.buyer or d.get('buyer', '')
            
            # Calculate ex-factory flag
            d['exfactory_flag'] = calculate_exfactory_flag(d.get("ex_factory_date", ""))

            # CONVERT DELIVERY DATE FOR HTML
            if d.get('delivery_date') and d['delivery_date'] != 'None':
               try:
            # Convert 16.12.2025 -> 2025-12-16
                  dt = datetime.strptime(d['delivery_date'], '%d.%m.%Y')
                  d['delivery_date_iso'] = dt.strftime('%Y-%m-%d')
               except:
                  d['delivery_date_iso'] = ""
            else:
                d['delivery_date_iso'] = ""

    # CONVERT GRN DATE FOR HTML
            if d.get('grn_date') and d['grn_date'] != 'None':
               try:
                  dt_grn = datetime.strptime(d['grn_date'], '%d.%m.%Y')
                  d['grn_date_iso'] = dt_grn.strftime('%Y-%m-%d')
               except:
                  d['grn_date_iso'] = ""
            else:
                d['grn_date_iso'] = ""
    
    # Convert dispatch date for HTML
            if d.get('dispatch_date'):
               try:
                  dt_disp = datetime.strptime(d['dispatch_date'], '%d.%m.%Y')
                  d['dispatch_date_iso'] = dt_disp.strftime('%Y-%m-%d')
               except:
                  d['dispatch_date_iso'] = ""
            else:
                d['dispatch_date_iso'] = ""

            
            
            d['parent_id'] = po_item.parent_id 
            d['child_seq'] = po_item.child_seq or 0
            
            processed.append(d)
        
        # Sort by Status (Pending first, Dispatched always at bottom), then Ex-Factory Date, then OCN
        def get_status_priority(status):
            """Returns priority: 0 for Pending, 1 for others, 2 for Dispatched (bottom most) 3 for Cancelled"""
            status = str(status or "").strip()
            if status == "Pending":
                return 0  # Pending items first
            elif status == "Dispatched":
                return 2  # Dispatched always at the bottom
            elif status == "Cancelled":
                return 3  # Moved to 3 to be last
            else:
                return 1  # Cancelled and other statuses in between
        
        processed.sort(key=lambda x: (
            get_status_priority(x.get("status", "Pending")),  # Status priority first (Pending=0, Others=1, Dispatched=2)
            parse_exfactory_date_for_sort(x.get("ex_factory_date", "")) or datetime.max,  # Then Ex-Factory Date (earliest first)
            x.get("parent_id") or x.get("id"),                 # 4️⃣ Group children under parent
             x.get("parent_id") is not None,                    # 3️⃣ Parent first, children next
              x.get("child_seq", 0), 
            x.get("ocn", "") or ""  # Then OCN
        ))
    
    return render_template(
        "dashboard.html",
        data=processed,
        factories=FACTORIES,
        transporters=TRANSPORTERS,
        current_user=get_current_user()  
 )
    
   

@dashboard_bp.route('/pending-summary')
@login_required
def pending_summary():
    from collections import defaultdict
    with get_db_session() as session:
        # Fetch all pending items
        pending_items = session.query(POItem).filter(POItem.status == 'Pending').all()
        
        # This will store totals like: {"Style1": {"January 2026": 500, "February 2026": 200}}
        style_summary = defaultdict(lambda: defaultdict(int))
        all_months = set()
        style_details = {} # To store Buyer and Description for each style

        for item in pending_items:
            # Create the Month Key
            try:
                date_obj = datetime.strptime(item.ex_factory_date, '%d.%m.%Y')
                month_key = date_obj.strftime('%B %Y')
            except:
                month_key = "No Date"
            
            style_key = item.style_no or "Unknown"
            all_months.add(month_key)
            
            # Add to the specific month total for this style
            style_summary[style_key][month_key] += (item.quantity or 0)
            
            # Save metadata
            if style_key not in style_details:
                style_details[style_key] = {
                    'buyer': item.buyer,
                    'description': item.description
                }

        # Sort months chronologically
        sorted_months = sorted(list(all_months), 
                               key=lambda x: datetime.strptime(x, '%B %Y') if x != "No Date" else datetime.max)

        return render_template('pending_summary.html', 
                               style_summary=style_summary, 
                               style_details=style_details,
                               months=sorted_months)

@dashboard_bp.route('/update_field', methods=['POST'])
@login_required
def update_field():
    data = request.get_json()
    # Support both naming conventions for the ID
    row_id = data.get('row_id') or data.get('id')
    field = data.get('field')
    value = data.get('value')

    if not row_id or not field:
        return jsonify({"ok": False, "error": "Missing row_id or field"}), 400

    with get_db_session() as session:
        po_item = session.query(POItem).get(row_id)
        if not po_item:
            return jsonify({"ok": False, "error": "Item not found"}), 404

        response_data = {"ok": True}

        # --- 1. DATA SAVING SECTION (Matched to POItem Model) ---
        if field == "status":
            po_item.status = value
            response_data["new_status"] = value
            
        elif field == "factory_remarks":
            # Corrected: Maps to the actual model column 'factory_remarks'
            po_item.factory_remarks = value
            print(f"DEBUG: Saved factory_remarks")

        # Handles Text fields that match model names exactly
        elif field in ["transporter", "ocn", "factory"]:
            setattr(po_item, field, value if value else None)
            print(f"DEBUG: Saved {field}")

        elif field == "dispatch_date":
            if value and value.strip():
                try:
                    # Formats HTML date (YYYY-MM-DD) to DB dotted format (DD.MM.YYYY)
                    dt_obj = datetime.strptime(value, '%Y-%m-%d')
                    po_item.dispatch_date = dt_obj.strftime('%d.%m.%Y')
                    print(f"DEBUG: Saved dispatch_date: {po_item.dispatch_date}")
                except Exception as e:
                    print(f"Date Error: {e}")
            else:
                po_item.dispatch_date = ""

        elif field in ["quantity", "caselot", "dispatched_box"]:
            try:
                setattr(po_item, field, int(value) if value else 0)
            except: pass
            
        elif field == "grn_date":
            if value:
                try:
                    dt_obj = datetime.strptime(value, '%Y-%m-%d')
                    po_item.grn_date = dt_obj.strftime('%d.%m.%Y')
                    po_item.grn_status = "Cleared"
                except: pass
            else:
                po_item.grn_date = None
                po_item.grn_status = "Pending"
            response_data["new_grn_status"] = po_item.grn_status
         
        elif field == "po_date":
           if value and value.strip():
               try:
                  # Accept DD.MM.YYYY or YYYY-MM-DD
                  if "-" in value:
                      dt = datetime.strptime(value, "%Y-%m-%d")
                  else:
                      dt = datetime.strptime(value, "%d.%m.%Y")

                  po_item.po_date = dt.strftime("%d.%m.%Y")
               except Exception as e:
                  print("PO DATE ERROR:", e)
           else:
               po_item.po_date = ""


        # --- 2. FORMULA SECTION ---
        # Recalculate Ex-Factory for Delivery Date changes
        if field == "delivery_date":
            if value and value.strip():
                try:
                    dt_obj = datetime.strptime(value, '%Y-%m-%d')
                    dotted_date = dt_obj.strftime('%d.%m.%Y')
                    po_item.delivery_date = dotted_date
                    po_item.delivery_month = calc_delivery_month(dotted_date)
                    # Uses your instruction: Location-based days subtraction
                    po_item.ex_factory_date = calc_ex_factory(po_item.location, dotted_date)
                    
                    response_data["new_month"] = po_item.delivery_month
                    response_data["new_ex_factory"] = po_item.ex_factory_date
                except Exception as e:
                    print(f"Date Error: {e}")

        # Recalculate Math for Qty/Caselot changes
        if field in ["quantity", "caselot", "dispatched_box"]:
            q = int(po_item.quantity or 0)
            c = int(po_item.caselot or 0)
            db = int(po_item.dispatched_box or 0)

            po_item.no_of_boxes = calc_no_of_boxes(c, q)
            po_item.dispatched_qty = db * c
            po_item.balance = max(0, q - po_item.dispatched_qty)

            response_data.update({
                "new_boxes": po_item.no_of_boxes,
                "dispatched_qty": po_item.dispatched_qty,
                "balance": po_item.balance
            })

        session.commit()
        return jsonify(response_data)