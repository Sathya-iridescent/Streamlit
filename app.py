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


 # --- TAB 3: UPLOAD ---
with tab3:
    st.header("📤 Upload Multiple PO PDFs")
    
    st.info("""
    **Instructions:**
    - Select one or more PDF files.
    - If a PO has multiple styles, all will be extracted.
    - Click 'Process All Files' to update the Dashboard.
    """)
    
    # 1. THE UPLOADER (This is the box you were missing)
    uploaded_files = st.file_uploader(
        "Select PDF Files", 
        accept_multiple_files=True, 
        type=['pdf'],
        key="po_file_uploader" # Unique key prevents UI glitches
    )
    
    # 2. THE PROCESS BUTTON
    if st.button("Process All Files", type="primary"):
        if uploaded_files:
            processed_count = 0
            with get_db_session() as session:
                for f in uploaded_files:
                    try:
                        file_bytes = f.getvalue()
                        doc = fitz.open(stream=file_bytes, filetype="pdf")
                        text_content = "".join(page.get_text() for page in doc)
                        
                        # Extract list of items (handles multiple styles/items per PO)
                        items = extract_items(text_content, f.name)
                        
                        if items:
                            # Cleanup: Remove old data for this specific PO 
                            # so we don't get duplicates if re-uploading
                            first_po = str(items[0].get('PO #', ''))
                            session.query(POItem).filter(POItem.po_number == first_po).delete()
                            
                            for item in items:
                                # Calculate Ex-Factory [cite: 2026-01-11]
                                ex_fty = apply_ex_factory_logic(
                                    item.get('Location', ''), 
                                    item.get('Delivery Date', '')
                                )
                                
                                # Add each style as a new row (using the Serial ID)
                                new_row = POItem(
                                    po_number=str(item.get('PO #', '')),
                                    ean=str(item.get('EAN NO', '')),
                                    delivery_date=item.get('Delivery Date', ''),
                                    ex_factory_date=ex_fty,
                                    location=item.get('Location', ''),
                                    quantity=int(item.get('Quantity', 0)),
                                    filename=f.name,
                                    status="Pending"
                                )
                                session.add(new_row)
                            
                            processed_count += 1
                        doc.close()
                        
                    except Exception as e:
                        st.error(f"Error processing {f.name}: {e}")
                
                # Final Save
                session.commit()
            
            if processed_count > 0:
                st.cache_data.clear() # Clear dashboard cache
                st.success(f"Successfully processed {processed_count} files!")
                st.rerun()
        else:
            st.warning("Please select at least one PDF file first.")



