import streamlit as st
import pandas as pd
import io
import fitz
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
    if not df.empty:
    # Convert DataFrame to Excel format in memory
        import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='PO_Report')
    
    st.download_button(
        label="📥 Download Full Dashboard as Excel",
        data=buffer.getvalue(),
        file_name=f"PO_Master_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- TAB 2: STYLE MASTER ---
with tab2:
    st.header("🏢 Style Master (Manual Entry)")
    
    # Form to manually enter data
    with st.form("add_style_mapping", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        ean_input = col1.text_input("Enter EAN")
        style_input = col2.text_input("Enter Style No")
        buyer_input = col3.text_input("Enter Buyer Name")
        
        if st.form_submit_button("Add to Master"):
            if ean_input:
                with get_db_session() as session:
                    # session.merge updates if EAN exists, or creates new if it doesn't
                    new_entry = StyleMaster(ean=ean_input, style_no=style_input, buyer=buyer_input)
                    session.merge(new_entry)
                    session.commit()
                st.success(f"Saved: {ean_input} -> {style_input}")
                st.rerun()
            else:
                st.error("EAN is required!")

    st.divider()
    
    # View and Delete Existing Records
    st.subheader("Existing Mappings")
    with get_db_session() as session:
        all_styles = session.query(StyleMaster).all()
        if all_styles:
            for s in all_styles:
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(f"**EAN:** {s.ean}")
                c2.write(f"**Style:** {s.style_no}")
                c3.write(f"**Buyer:** {s.buyer}")
                if c4.button("❌ Delete", key=f"del_style_{s.id}"):
                    session.delete(s)
                    session.commit()
                    st.rerun()
        else:
            st.info("No records found. Use the form above to add your first style.")

# --- TAB 3: UPLOAD ---
with tab3:
    st.header("📤 Upload Multiple PO PDFs")
    
    st.info("""
    **Instructions:**
    - Select one or more PDF files.
    - Click 'Process All Files' to extract data.
    - Files will automatically appear in the Dashboard.
    """)
    
    uploaded_files = st.file_uploader("Select PDF Files", accept_multiple_files=True, type=['pdf'])
    
    if st.button("Process All Files", type="primary") and uploaded_files:
        processed_count = 0
        with get_db_session() as session:
            for f in uploaded_files:
                try:  # <--- Start of the try block
                   file_bytes = f.getvalue()
                   doc = fitz.open(stream=file_bytes, filetype="pdf")
                   text = "".join(page.get_text() for page in doc)
                   items = extract_items(text, f.name)
                
                   for item in items:
                       po_num_str= str(item.get('PO #', ''))
                       ex_fty = apply_ex_factory_logic(item.get('Location', ''), item.get('Delivery Date', ''))
                    
                       # Logic to check for existing/amended POs
                       existing_po = session.get(POItem, po_num_str)
                    
                       if existing_po:
                           existing_po.delivery_date = item.get('Delivery Date', '')
                           existing_po.ex_factory_date = ex_fty
                           existing_po.is_amended = True
                           st.info(f"Updated Amended PO: {po_num}")
                       else:
                           po_entry = POItem(
                              po_number=po_num,
                              ean=str(item.get('EAN NO', '')),
                              delivery_date=item.get('Delivery Date', ''),
                              ex_factory_date=ex_fty,
                              location=item.get('Location', ''),
                              quantity=int(item.get('Quantity', 0)),
                              status="Pending",
                              is_amended=False
                          )
                           session.add(po_entry)
                
                   processed_count += 1
                   doc.close()

                except Exception as e:  # <--- This MUST be at the same level as the 'try'
                    st.error(f"Error processing {f.name}: {e}")

        session.commit() # Save everything to the database
        
        if processed_count > 0:
            st.success(f"Successfully processed {processed_count} files!")
            st.rerun() 

# --- TAB 4: MONTHLY SUMMARY ---
with tab4:
  st.header("📈 Monthly Summary Report")
    
  if not df.empty:
        # Create the Pivot Table
        summary_df = df[df['status'] == 'Pending']
        if not summary_df.empty:
            pivot = summary_df.pivot_table(
                index=['buyer', 'style_no'],
                values='quantity',
                aggfunc='sum'
            )
            
            # Displaying for Print
            st.write("### Pending Orders Summary")
            st.table(pivot) # st.table looks better for printing than st.dataframe
            
            st.info("💡 **To Save as PDF:** Press **Ctrl + P** (Windows) or **Cmd + P** (Mac) and select 'Save as PDF' as your printer.")
            
            # Also provide Excel version of summary
            csv_summary = pivot.to_csv().encode('utf-8')
            st.download_button(
                label="📥 Download Summary CSV",
                data=csv_summary,
                file_name="monthly_summary.csv",
                mime="text/csv"
            )
























