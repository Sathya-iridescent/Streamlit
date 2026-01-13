import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os, fitz

# Import your own logic
from database import get_db_session, initialize_db
from models import User, POItem, StyleMaster
from extractor import extract_items
from utils.helpers import calc_delivery_month, calc_no_of_boxes, calculate_exfactory_flag

# --- APP CONFIG ---
st.set_page_config(layout="wide", page_title="Iridescent PO Dashboard")
initialize_db()

def get_ex_factory_logic(loc, delv_date_str):
    """Applying your exact 2026-01-11 location rules"""
    try:
        # 1. Start with extracted date - 4 days
        dt = datetime.strptime(delv_date_str, "%d.%m.%Y") - timedelta(days=4)
        
        # 2. Subtract location specific days [cite: 2026-01-11]
        loc_lower = loc.lower()
        if "vadodara" in loc_lower: days = 6
        elif "bhiwandi" in loc_lower: days = 4
        elif any(x in loc_lower for x in ["mandal", "isnapur", "medak", "manoharabad"]): days = 3
        else: days = 0
        
        return (dt - timedelta(days=days)).strftime("%d.%m.%Y")
    except: return delv_date_str

# --- NAVIGATION ---
page = st.sidebar.selectbox("Menu", ["Dashboard", "Upload PO", "Style Master", "Pending Summary"])

if page == "Dashboard":
    st.title("📋 Operations Dashboard")
    with get_db_session() as session:
        # Join query to get Style info automatically
        data = session.query(POItem).all()
        if data:
            df = pd.DataFrame([i.to_dict() for i in data])
            # Add the Red/Yellow color flag logic
            df['flag'] = df['ex_factory_date'].apply(calculate_exfactory_flag)
            st.data_editor(df, use_container_width=True, hide_index=True)
        else:
            st.info("No POs found.")

elif page == "Upload PO":
    st.title("📤 PO Extraction")
    files = st.file_uploader("Upload DMart PDF", accept_multiple_files=True)
    if files:
        for f in files:
            # Save and parse text
            text = "".join(page.get_text() for page in fitz.open(stream=f.read(), filetype="pdf"))
            items = extract_items(text, f.name)
            
            with get_db_session() as session:
                for item in items:
                    ex_fty = get_ex_factory_logic(item['Location'], item['Delivery Date'])
                    new_item = POItem(
                        po_number=item['PO #'],
                        ean=item['EAN NO'],
                        delivery_date=item['Delivery Date'],
                        ex_factory_date=ex_fty, # Automated [cite: 2026-01-11]
                        status="Pending"
                    )
                    session.add(new_item)
                st.success(f"Processed {f.name}")

elif page == "Pending Summary":
    st.title("📊 Style-wise Monthly Summary")
    with get_db_session() as session:
        items = session.query(POItem).filter_by(status="Pending").all()
        if items:
            df = pd.DataFrame([i.to_dict() for i in items])
            summary = df.pivot_table(index='style_no', columns='delivery_month', values='quantity', aggfunc='sum')
            st.dataframe(summary.fillna(0))

elif page == "Style Master":
    st.title("🏢 EAN Style Mapping")
    # Table to edit Style No and Buyer for each EAN
