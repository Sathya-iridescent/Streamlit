import streamlit as st
import pandas as pd
import io
import fitz  # PyMuPDF
from datetime import datetime, timedelta
from database import get_db_session
from models import POItem, StyleMaster
from extractor import extract_items
from utils.helpers import calculate_exfactory_flag, calc_no_of_boxes

# --- 1. CONFIG & STYLING (Matching your CSS) ---
st.set_page_config(layout="wide", page_title="PO Operations Master")

st.markdown("""
<style>
    .main { background-color: #E9F4FF; }
    /* Summary Bar Styling */
    .metric-container {
        background-color: white;
        padding: 15px;
        border: 1px solid #0074D9;
        border-radius: 6px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #0074D9 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. CORE LOGIC [cite: 2026-01-11] ---
def apply_ex_factory_logic(location, delivery_date_str):
    """Applies your specific location-based days calculation"""
    try:
        dt = datetime.strptime(delivery_date_str, "%d.%m.%Y")
        loc = (location or "").lower()
        
        if "vadodara" in loc: days = 6
        elif "bhiwandi" in loc: days = 4
        elif any(x in loc for x in ["mandal", "isnapur", "medak", "manoharabad"]): days = 3
        else: days = 0 # Default/Others
        
        ex_fact = dt - timedelta(days=days)
        return ex_fact.strftime("%d.%m.%Y")
    except:
        return delivery_date_str

def get_row_colors(row):
    """Replicates your priority highlighting: Red > Yellow > Orange"""
    flag = calculate_exfactory_flag(row['ex_factory_date'])
    
    if flag == 'overdue' and row['status'] == 'Pending':
        return ['background-color: #FA002F; color: white'] * len(row)
    if flag == 'due-soon' and row['status'] == 'Pending':
        return ['background-color: #FFF3B0; color: black'] * len(row)
    if row.get('is_amended'):
        return ['background-color: #FF8300; color: white'] * len(row)
    if row['status'] == 'Dispatched':
        return ['background-color: #D3D3D3; color: #333'] * len(row)
    return [''] * len(row)

# --- 3. UI TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🏢 Style Master", "📤 Upload POs", "📈 Monthly Summary"])

# --- DASHBOARD TAB ---
with tab1:
    st.title("PO Dashboard")
    
    with get_db_session() as session:
        # Replicating your JOIN logic to get Style/Buyer names
        query = session.query(POItem, StyleMaster).outerjoin(StyleMaster, POItem.ean == StyleMaster.ean).all()
        
        data = []
        for po, style in query:
            d = po.to_dict()
            if style:
                d['buyer'] = style.buyer
                d['style_no'] = style.style_no
            data.append(d)
        
        if data:
            df = pd.DataFrame(data)
            
            # Summary Bar (Total Qty, OCN Count)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total POs", len(df))
            c2.metric("Total Qty", f"{df['quantity'].sum():,}")
            c3.metric("OCN Count", len(df[df['ocn'] != ""]))

            # The Interactive Table (Replaces JS Update Engine)
            edited_df = st.data_editor(
                df.style.apply(get_row_colors, axis=1),
                column_config={
                    "status": st.column_config.SelectboxColumn("Status", options=["Pending", "Dispatched", "Cancelled"]),
                    "factory": st.column_config.SelectboxColumn("Factory", options=["Factory A", "Factory B"]),
                    "quantity": st.column_config.NumberColumn("Qty"),
                    "dispatched_box": st.column_config.NumberColumn("Disp. Box")
                },
                hide_index=True,
                use_container_width=True
            )

            if st.button("💾 Save Changes"):
                for _, row in edited_df.iterrows():
                    item = session.query(POItem).get(row['id'])
                    if item:
                        item.status = row['status']
                        item.factory_remarks = row['factory_remarks']
                        item.quantity = row['quantity']
                        item.dispatched_box = row['dispatched_box']
                        # Auto-Math
                        item.no_of_boxes = calc_no_of_boxes(item.caselot, item.quantity)
                        item.dispatched_qty = item.dispatched_box * item.caselot
                        item.balance = item.quantity - item.dispatched_qty
                st.success("Changes Saved!")
                st.rerun()
        else:
            st.info("No data yet. Go to Upload tab.")

# --- STYLE MASTER TAB ---
with tab2:
    st.header("Style Master")
    with st.form("add_style"):
        c1, c2, c3 = st.columns(3)
        ean = c1.text_input("EAN")
        style = c2.text_input("Style")
        buyer = c3.selectbox("Buyer", ["", "Buyer A", "Buyer B", "Buyer C"])
        if st.form_submit_button("Add Record"):
            with get_db_session() as session:
                session.merge(StyleMaster(ean=ean, style_no=style, buyer=buyer))
                st.success("EAN Registered!")
                st.rerun()

# --- UPLOAD TAB ---
with tab3:
    st.header("Upload PO PDFs")
    files = st.file_uploader("Select PDFs", accept_multiple_files=True, type=['pdf'])
    if st.button("Process All Files") and files:
        with get_db_session() as session:
            for f in files:
                doc = fitz.open(stream=f.read(), filetype="pdf")
                text = "".join(p.get_text() for p in doc)
                extracted_items = extract_items(text, f.name)
                
                for item in extracted_items:
                    # Apply your location rule [cite: 2026-01-11]
                    ex_fty = apply_ex_factory_logic(item['Location'], item['Delivery Date'])
                    
                    po_entry = POItem(
                        po_number=item['PO #'],
                        ean=item['EAN NO'],
                        delivery_date=item['Delivery Date'],
                        ex_factory_date=ex_fty,
                        location=item['Location'],
                        quantity=item.get('Quantity', 0),
                        status="Pending"
                    )
                    session.merge(po_entry)
            st.success("Upload Complete!")

# --- MONTHLY SUMMARY TAB ---
with tab4:
    st.header("Pending Summary By Month")
    # Pivot logic from your summary template
    if not df.empty:
        summary_df = df[df['status'] == 'Pending']
        if not summary_df.empty:
            pivot = summary_df.pivot_table(
                index=['buyer', 'style_no'], 
                columns='delivery_month', 
                values='quantity', 
                aggfunc='sum', 
                fill_value=0
            )
            st.dataframe(pivot, use_container_width=True)
            if st.button("Print View"):
                st.write("Press Ctrl+P to save as PDF")
