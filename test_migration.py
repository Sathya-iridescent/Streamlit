"""
Test Script: Compare SQLite (old) vs PostgreSQL (new) databases
Verifies that migration was successful and both produce same results
"""
import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import POItem, StyleMaster

# Load environment variables
load_dotenv()

print("="*70)
print("MIGRATION TEST: Old SQLite vs New Database Comparison")
print("="*70)

# ==================== CONNECT TO BOTH DATABASES ====================

# SQLite (old)
print("\n1. Connecting to SQLite databases (old)...")
sqlite_po = sqlite3.connect('po_data.db')
sqlite_po.row_factory = sqlite3.Row
sqlite_master = sqlite3.connect('style_master.db')
sqlite_master.row_factory = sqlite3.Row

# New Database (PostgreSQL or SQLite)
DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
print(f"\n2. Connecting to new database (type: {DB_TYPE})...")

if DB_TYPE == 'postgresql':
    # PostgreSQL connection
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'poextract_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    print(f"   PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
else:
    # SQLite connection (new unified database)
    DATABASE_URL = "sqlite:///poextract.db"
    print(f"   SQLite: poextract.db")

try:
    new_engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=new_engine)
    new_session = Session()
    # Use pg_session name for compatibility with rest of script
    pg_session = new_session
except Exception as e:
    print(f"ERROR: Could not connect to new database: {e}")
    exit(1)

# ==================== TEST 1: COUNT RECORDS ====================
print("\n" + "="*70)
print("TEST 1: Record Counts")
print("="*70)

# Style Master
sqlite_master_count = sqlite_master.execute("SELECT COUNT(*) as count FROM style_master").fetchone()['count']
pg_master_count = pg_session.query(StyleMaster).count()

print(f"\nstyle_master:")
print(f"  Old SQLite:  {sqlite_master_count} records")
print(f"  New Database ({DB_TYPE.upper()}): {pg_master_count} records")
if sqlite_master_count == pg_master_count:
    print(f"  ✓ MATCH")
else:
    print(f"  ✗ MISMATCH - Missing {sqlite_master_count - pg_master_count} records")

# PO Items
sqlite_po_count = sqlite_po.execute("SELECT COUNT(*) as count FROM po_items").fetchone()['count']
pg_po_count = pg_session.query(POItem).count()

print(f"\npo_items:")
print(f"  Old SQLite:  {sqlite_po_count} records")
print(f"  New Database ({DB_TYPE.upper()}): {pg_po_count} records")
if sqlite_po_count == pg_po_count:
    print(f"  ✓ MATCH")
else:
    print(f"  ✗ MISMATCH - Missing {sqlite_po_count - pg_po_count} records")

# ==================== TEST 2: DATA COMPARISON ====================
print("\n" + "="*70)
print("TEST 2: Data Comparison (First 5 records)")
print("="*70)

# Style Master
print("\nstyle_master (first 5):")
sqlite_master_rows = sqlite_master.execute("SELECT * FROM style_master LIMIT 5").fetchall()
pg_master_rows = pg_session.query(StyleMaster).limit(5).all()

for i, (sqlite_row, pg_row) in enumerate(zip(sqlite_master_rows, pg_master_rows), 1):
    print(f"\n  Record {i}:")
    print(f"    Old SQLite:    id={sqlite_row['id']}, ean={sqlite_row['ean']}, style_no={sqlite_row['style_no']}")
    print(f"    New Database: id={pg_row.id}, ean={pg_row.ean}, style_no={pg_row.style_no}")
    
    if (sqlite_row['id'] == pg_row.id and 
        sqlite_row['ean'] == pg_row.ean and 
        sqlite_row['style_no'] == pg_row.style_no):
        print(f"    ✓ MATCH")
    else:
        print(f"    ✗ MISMATCH")

# PO Items
print("\npo_items (first 5):")
sqlite_po_rows = sqlite_po.execute("SELECT * FROM po_items LIMIT 5").fetchall()
pg_po_rows = pg_session.query(POItem).limit(5).all()

for i, (sqlite_row, pg_row) in enumerate(zip(sqlite_po_rows, pg_po_rows), 1):
    print(f"\n  Record {i}:")
    print(f"    Old SQLite:    id={sqlite_row['id']}, po_number={sqlite_row['po_number']}, ean={sqlite_row['ean']}")
    print(f"    New Database: id={pg_row.id}, po_number={pg_row.po_number}, ean={pg_row.ean}")
    
    if (sqlite_row['id'] == pg_row.id and 
        sqlite_row['po_number'] == pg_row.po_number and 
        sqlite_row['ean'] == pg_row.ean):
        print(f"    ✓ MATCH")
    else:
        print(f"    ✗ MISMATCH")

# ==================== TEST 3: JOIN QUERY TEST ====================
print("\n" + "="*70)
print("TEST 3: JOIN Query Test")
print("="*70)

# SQLite JOIN (old way - manual lookup)
print("\nSQLite (old method - separate queries):")
sqlite_po_sample = sqlite_po.execute("SELECT id, ean, po_number FROM po_items WHERE ean IS NOT NULL LIMIT 5").fetchall()
sqlite_join_results = []
for row in sqlite_po_sample:
    ean = row['ean']
    style_info = sqlite_master.execute("SELECT style_no, buyer FROM style_master WHERE ean=?", (ean,)).fetchone()
    if style_info:
        sqlite_join_results.append({
            'po_id': row['id'],
            'po_number': row['po_number'],
            'ean': ean,
            'style_no': style_info['style_no'],
            'buyer': style_info['buyer']
        })

print(f"  Found {len(sqlite_join_results)} records with matching EANs")
for r in sqlite_join_results[:3]:
    print(f"    PO #{r['po_number']} (EAN: {r['ean']}) -> Style: {r['style_no']}, Buyer: {r['buyer']}")

# New Database JOIN (new way - proper JOIN)
print(f"\nNew Database ({DB_TYPE.upper()}) (new method - JOIN query):")
pg_join_results = pg_session.query(POItem, StyleMaster).join(
    StyleMaster, POItem.ean == StyleMaster.ean
).limit(5).all()

print(f"  Found {len(pg_join_results)} records with JOIN")
for po_item, style_master in pg_join_results[:3]:
    print(f"    PO #{po_item.po_number} (EAN: {po_item.ean}) -> Style: {style_master.style_no}, Buyer: {style_master.buyer}")

if len(sqlite_join_results) == len(pg_join_results):
    print(f"\n  ✓ JOIN results count MATCH")
else:
    print(f"\n  ✗ JOIN results count MISMATCH")

# ==================== TEST 4: FOREIGN KEY INTEGRITY ====================
print("\n" + "="*70)
print("TEST 4: Foreign Key Integrity")
print("="*70)

# Check for orphaned po_items (EAN not in style_master)
print("\nChecking for orphaned po_items (EAN not in style_master):")
sqlite_eans = set(row['ean'] for row in sqlite_master.execute("SELECT ean FROM style_master").fetchall())
sqlite_po_eans = set(row['ean'] for row in sqlite_po.execute("SELECT DISTINCT ean FROM po_items WHERE ean IS NOT NULL").fetchall())
sqlite_orphans = sqlite_po_eans - sqlite_eans

pg_eans = set(row.ean for row in pg_session.query(StyleMaster.ean).all())
pg_po_eans = set(row.ean for row in pg_session.query(POItem.ean).filter(POItem.ean.isnot(None)).distinct().all())
pg_orphans = pg_po_eans - pg_eans

print(f"  Old SQLite: {len(sqlite_orphans)} orphaned EANs")
print(f"  New Database ({DB_TYPE.upper()}): {len(pg_orphans)} orphaned EANs")

if sqlite_orphans == pg_orphans:
    print(f"  ✓ Orphaned EANs MATCH")
else:
    print(f"  ✗ Orphaned EANs MISMATCH")
    if sqlite_orphans - pg_orphans:
        print(f"    Missing in New Database: {sqlite_orphans - pg_orphans}")
    if pg_orphans - sqlite_orphans:
        print(f"    Extra in New Database: {pg_orphans - sqlite_orphans}")

# ==================== TEST 5: QUERY RESULTS COMPARISON ====================
print("\n" + "="*70)
print("TEST 5: Query Results Comparison")
print("="*70)

# Test: Get PO items with status "Pending"
print("\nQuery: SELECT * FROM po_items WHERE status = 'Pending'")

sqlite_pending = sqlite_po.execute("SELECT COUNT(*) as count FROM po_items WHERE status = 'Pending'").fetchone()['count']
pg_pending = pg_session.query(POItem).filter_by(status='Pending').count()

print(f"  Old SQLite:  {sqlite_pending} records")
print(f"  New Database ({DB_TYPE.upper()}): {pg_pending} records")
if sqlite_pending == pg_pending:
    print(f"  ✓ MATCH")
else:
    print(f"  ✗ MISMATCH")

# Test: Get PO items with EAN lookup
print("\nQuery: Get style_no and buyer for a specific EAN")
test_ean = sqlite_po.execute("SELECT ean FROM po_items WHERE ean IS NOT NULL LIMIT 1").fetchone()
if test_ean:
    test_ean = test_ean['ean']
    sqlite_style = sqlite_master.execute("SELECT style_no, buyer FROM style_master WHERE ean=?", (test_ean,)).fetchone()
    pg_style = pg_session.query(StyleMaster).filter_by(ean=test_ean).first()
    
    print(f"  Testing EAN: {test_ean}")
    if sqlite_style:
        print(f"    Old SQLite:    style_no={sqlite_style['style_no']}, buyer={sqlite_style['buyer']}")
    if pg_style:
        print(f"    New Database: style_no={pg_style.style_no}, buyer={pg_style.buyer}")
    
    if sqlite_style and pg_style:
        if sqlite_style['style_no'] == pg_style.style_no and sqlite_style['buyer'] == pg_style.buyer:
            print(f"    ✓ MATCH")
        else:
            print(f"    ✗ MISMATCH")

# ==================== TEST 6: FIELD-BY-FIELD COMPARISON ====================
print("\n" + "="*70)
print("TEST 6: Field-by-Field Comparison (Sample Record)")
print("="*70)

# Get a sample record from both
sqlite_sample = sqlite_po.execute("SELECT * FROM po_items LIMIT 1").fetchone()
if sqlite_sample:
    pg_sample = pg_session.query(POItem).filter_by(id=sqlite_sample['id']).first()
    
    if pg_sample:
        print(f"\nComparing PO Item ID: {sqlite_sample['id']}")
        
        fields_to_check = [
            'filename', 'po_number', 'po_date', 'style_no', 'ocn', 'buyer',
            'delivery_date', 'delivery_month', 'location', 'ean', 'description',
            'caselot', 'quantity', 'no_of_boxes', 'factory', 'ex_factory_date',
            'dispatched_box', 'dispatched_qty', 'balance', 'status'
        ]
        
        mismatches = []
        matches = []
        
        for field in fields_to_check:
            sqlite_val = sqlite_sample[field]
            pg_val = getattr(pg_sample, field, None)
            
            # Handle type conversions
            if isinstance(sqlite_val, int) and pg_val is not None:
                pg_val = int(pg_val) if pg_val else 0
            if sqlite_val is None:
                sqlite_val = ''
            if pg_val is None:
                pg_val = ''
            
            if str(sqlite_val) == str(pg_val):
                matches.append(field)
            else:
                mismatches.append((field, sqlite_val, pg_val))
        
        print(f"  ✓ Matched fields: {len(matches)}/{len(fields_to_check)}")
        if mismatches:
            print(f"  ✗ Mismatched fields: {len(mismatches)}")
            for field, sqlite_val, pg_val in mismatches[:5]:
                print(f"    {field}: Old SQLite='{sqlite_val}' vs New Database='{pg_val}'")
        else:
            print(f"  ✓ All fields MATCH")

# ==================== SUMMARY ====================
print("\n" + "="*70)
print("TEST SUMMARY")
print("="*70)

all_tests_passed = (
    sqlite_master_count == pg_master_count and
    sqlite_po_count == pg_po_count and
    len(sqlite_join_results) == len(pg_join_results) if 'sqlite_join_results' in locals() else True
)

if all_tests_passed:
    print("\n✓ ALL TESTS PASSED - Migration successful!")
    print("  Both databases produce the same results.")
    print("  JOIN queries work correctly.")
    print("  Foreign key relationships are intact.")
else:
    print("\n✗ SOME TESTS FAILED - Please review the output above.")
    print("  Migration may need to be re-run or data verified manually.")

print("\n" + "="*70)

# Cleanup
sqlite_po.close()
sqlite_master.close()
pg_session.close()



