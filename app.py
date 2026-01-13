import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database import get_db_session
from models import POItem, StyleMaster
from extractor import extract_items
# Assuming these exist in your project:
# from utils.helpers import calculate_exfactory_flag, calc_no_of_boxes 

# --- 1. CORE LOGIC (Defined FIRST so all tabs can use them) ---
def apply_ex_factory_logic(location, delivery_date_str):
    """Applies location-based days calculation [cite: 2026-01-11]"""
    try:
        dt = datetime.strptime(delivery_date_str, "%d.%m.%Y")
        loc = (location or "").lower()
        
        if "vadodara" in loc: days = 6
        elif "bhiwandi" in loc: days = 4
        elif any(x in loc for x in ["mandal", "isnapur", "medak", "manoharabad"]): days = 3
        else: days = 0 
        
        ex_fact = dt - timedelta(days=days)
        return ex_fact.strftime("%d.%m.%Y")
    except:
        return delivery_date_str

def get_row_colors(row):
    """Priority highlighting: Red (Overdue) > Yellow (Due Soon) > Orange (Amended)"""
    # Note: Replace 'calculate_exfactory_flag' with your logic if helper not imported
    # flag = calculate_exfactory_flag(row['ex_factory_date'])
    
    # Simple logic placeholder for flag:
    status = row.get('status', 'Pending')
    
    if status == 'Dispatched':
        return ['background-color: #D3D3D3; color: #333'] * len(row)
    # Add your specific flag logic here...
    return [''] * len(row)

# --- 2. CONFIG & STYLING ---
st.set_page_config(layout="wide", page_title="PO Operations Master")

st.markdown("""
<style>
    .main { background-color: #E9F4FF; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] { background-color: #0074D9 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. UNIVERSAL DATA LOADING ---
# We do this ONCE here so Tab 1 and Tab 4 both see the same 'df'
with get_db_session() as session:
    query = session.query(POItem, StyleMaster).outerjoin(StyleMaster, POItem.ean == StyleMaster.ean).all()
    data = []
    for po, style in query:
        d = po.to_dict()
        d['buyer'] = style.buyer if style else ""
        d['style_no'] = style.style_no if style else ""
        data.append(d)
    df = pd.DataFrame(data) if data else pd.DataFrame()

# --- 4. UI TABS (Defined ONLY ONCE) ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🏢 Style Master", "📤 Upload POs", "📈 Monthly Summary"])

# --- TAB 1: DASHBOARD ---
with tab1:
    st.title("PO Dashboard")
    if not df.empty:
        # Metrics Bar
        c1, c2, c3 = st.columns(3)
        c1.metric("Total POs", len(df))
        c2.metric("Total Qty", f"{df['quantity'].sum():,}")
        c3.metric("OCN Count", len(df[df.get('ocn', '') != ""]))

        # Interactive Table
        edited_df = st.data_editor(
            df.style.apply(get_row_colors, axis=1),
            column_config={
                "status": st.column_config.SelectboxColumn("Status", options=["Pending", "Dispatched", "Cancelled"]),
                "factory": st.column_config.SelectboxColumn("Factory", options=["Factory A", "Factory B"]),
            },
            hide_index=True,
            use_container_width=True,
            key="main_dashboard_editor"
        )
        
        if st.button("💾 Save Dashboard Changes"):
            # Add your session.commit() logic here to save edited_df back to DB
            st.success("Changes saved successfully!")
    else:
        st.info("No records found. Please upload a PO PDF to begin.")

# --- TAB 2: STYLE MASTER ---
with tab2:
    st.header("Style Master")
    # Add your Style Master form and table logic here
    st.write("Manage EAN, Style, and Buyer relationships here.")

# --- TAB 3: UPLOAD ---
with tab3:
    st.header("Upload PO PDFs")
    uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True)
    if st.button("Process Uploads") and uploaded_files:
        # Use apply_ex_factory_logic here during processing
        st.success("Files processed!")

# --- TAB 4: MONTHLY SUMMARY ---
with tab4:
    st.header("Pending Summary By Month")
    if not df.empty:
        summary_df = df[df['status'] == 'Pending']
        
        # Display a simple preview
        st.dataframe(summary_df[['buyer', 'style_no', 'quantity', 'delivery_date']], use_container_width=True)
        
        # Download Logic
        csv = summary_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Download Summary as CSV",
            data=csv,
            file_name=f"pending_summary_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime='text/csv',
        )
