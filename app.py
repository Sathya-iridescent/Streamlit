import streamlit as st
import pandas as pd
import fitz
import io
from datetime import datetime, timedelta
from sqlalchemy import text

# Import from your database and models
from database import get_db_session, engine
from models.po_item import POItem, StyleMaster, Base
from extractor import extract_items

# --- 1. CORE LOGIC ---
def apply_ex_factory_logic(location, delivery_date_str):
    """Calculates date based on location days [cite: 2026-01-11]"""
    try:
        dt = datetime.strptime(delivery_date_str, "%d.%m.%Y")
        loc = (location or "").lower()
        if "vadodara" in loc: days = 6
        elif "bhiwandi" in loc: days = 4
        elif any(x in loc for x in ["mandal", "isnapur", "medak", "manoharabad"]): days = 3
        else: days = 0 
        return (dt - timedelta(days=days)).strftime("%d.%m.%Y")
    except:
        return delivery_date_str

def get_row_colors(row):
    """Priority: Dispatched (Grey) > Overdue (Red) > Due Soon (Yellow) > Amended (Orange)"""
    status = row.get('status', 'Pending')
    if status == 'Dispatched': return ['background-color: #D3D3D3'] * len(row)
    
    try:
        today = datetime.now().date()
        ex_fty = datetime.strptime(row.get('ex_factory_date', ''), "%d.%m.%Y").date()
        diff = (ex_fty - today).days
        if diff < 0: return ['background-color: #FA002F; color: white'] * len(row)
        if 0 <= diff <= 3: return ['background-color: #FFFF00; color: black'] * len(row)
    except: pass

    if row.get('is_amended'): return ['background-color: #FF8300; color: white'] * len(row)
    return [''] * len(row)

# --- 2. CONFIG & UI ---
st.set_page_config(layout="wide", page_title="PO Master")

# Emergency Repair Button in Sidebar
with st.sidebar:
    if st.button("⚠️ EMERGENCY: Reset Database"):
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS po_items CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS style_master CASCADE"))
            conn.commit()
        Base.metadata.create_all(engine)
        st.success("Database Rebuilt! Please refresh.")
        st.rerun()

# --- 3. DATA LOADING ---
@st.cache_data(ttl=60)
def load_full_data():
    with get_db_session() as session:
        query = session.query(POItem, StyleMaster).outerjoin(
            StyleMaster, POItem.ean == StyleMaster.ean).all()
        data = []
        for po, style in query:
            d = po.to_dict()
            d['buyer'] = style.buyer if style else d.get('buyer', '')
            d['style_no'] = style.style_no if style else d.get('style_no', '')
            data.append(d)
        return pd.DataFrame(data)

df = load_full_data()

# --- 4. TABS ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🏢 Style Master", "📤 Upload POs"])

with tab1:
    st.title("PO Dashboard")
    if not df.empty:
        st.data_editor(df.style.apply(get_row_colors, axis=1), use_container_width=True, hide_index=True)
    else:
        st.info("No data found. Please upload a PDF.")

with tab2:
    st.header("Style Master")
    with st.form("style_form"):
        c1, c2, c3 = st.columns(3)
        ean = c1.text_input("EAN")
        style = c2.text_input("Style No")
        buyer = c3.text_input("Buyer")
        if st.form_submit_button("Save Style"):
            with get_db_session() as session:
                session.merge(StyleMaster(ean=ean, style_no=style, buyer=buyer))
                session.commit()
            st.cache_data.clear()
            st.rerun()

with tab3:
    st.header("Upload POs")
    files = st.file_uploader("Select PDFs", accept_multiple_files=True, type=['pdf'])
    if st.button("Process Files") and files:
        with get_db_session() as session:
            for f in files:
                doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                text_content = "".join(page.get_text() for page in doc)
                items = extract_items(text_content, f.name)
                for item in items:
                    po_id = str(item.get('PO #', ''))
                    ex_fty = apply_ex_factory_logic(item.get('Location', ''), item.get('Delivery Date', ''))
                    
                    existing = session.get(POItem, po_id)
                    if existing:
                        existing.is_amended = True
                        existing.delivery_date = item.get('Delivery Date')
                        existing.ex_factory_date = ex_fty
                    else:
                        session.add(POItem(
                            id=po_id, po_number=po_id,
                            ean=str(item.get('EAN NO', '')),
                            delivery_date=item.get('Delivery Date'),
                            ex_factory_date=ex_fty,
                            location=item.get('Location'),
                            quantity=int(item.get('Quantity', 0))
                        ))
            session.commit()
        st.cache_data.clear()
        st.success("Done!")
        st.rerun()
