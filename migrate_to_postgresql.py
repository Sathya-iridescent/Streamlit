"""
Migration Script: SQLite → PostgreSQL
Migrates data from po_data.db and style_master.db to single PostgreSQL database
"""
import sqlite3
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker
from database import POItem, StyleMaster, Base

# Load environment variables
load_dotenv()

# SQLite connections
sqlite_po = sqlite3.connect('po_data.db')
sqlite_po.row_factory = sqlite3.Row

sqlite_master = sqlite3.connect('style_master.db')
sqlite_master.row_factory = sqlite3.Row

# PostgreSQL connection
DB_TYPE = os.getenv('DB_TYPE', 'postgresql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'poextract_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

if DB_TYPE != 'postgresql':
    print("ERROR: DB_TYPE must be 'postgresql' for migration")
    exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Connecting to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")
pg_engine = create_engine(DATABASE_URL)
Base.metadata.create_all(pg_engine)

Session = sessionmaker(bind=pg_engine)
pg_session = Session()

try:
    # Migrate style_master (id is primary key, ean is unique)
    print("\n1. Migrating style_master...")
    master_rows = sqlite_master.execute("SELECT * FROM style_master").fetchall()
    migrated_master = 0
    
    for row in master_rows:
        # id is primary key, ean is unique (used for foreign key)
        style = StyleMaster(
            id=row['id'],
            ean=row['ean'],
            style_no=row['style_no'],
            buyer=row['buyer']
        )
        pg_session.merge(style)  # Use merge to handle duplicates
        migrated_master += 1
    
    pg_session.commit()
    print(f"   ✓ Migrated {migrated_master} style_master records")

    # Migrate po_items
    print("\n2. Migrating po_items...")
    po_rows = sqlite_po.execute("SELECT * FROM po_items").fetchall()
    migrated_po = 0
    orphaned_eans = set()
    
    # Get all EANs that exist in style_master
    existing_eans = set(ean for ean, in pg_session.query(StyleMaster.ean).all())
    
    # Collect all unique EANs from po_items
    all_eans_from_po = set()
    for row in po_rows:
        if row['ean']:
            all_eans_from_po.add(row['ean'])
    
    # Create placeholder style_master entries for EANs that don't exist
    missing_eans = all_eans_from_po - existing_eans
    if missing_eans:
        print(f"   Creating {len(missing_eans)} placeholder style_master entries for orphaned EANs...")
        for ean in missing_eans:
            placeholder = StyleMaster(
                ean=ean,
                style_no="",  # Empty, can be filled later
                buyer=""      # Empty, can be filled later
            )
            pg_session.merge(placeholder)
        pg_session.commit()
        print(f"   ✓ Created placeholder entries")
    
    for row in po_rows:
        ean_value = row['ean']
        
        po_item = POItem(
            id=row['id'],
            filename=row['filename'],
            po_number=row['po_number'],
            po_date=row['po_date'],
            style_no=row['style_no'],
            ocn=row['ocn'],
            buyer=row['buyer'],
            delivery_date=row['delivery_date'],
            delivery_month=row['delivery_month'],
            location=row['location'],
            ean=ean_value,  # Foreign key to style_master (NULL if not in style_master)
            description=row['description'],
            caselot=row['caselot'],
            quantity=row['quantity'],
            no_of_boxes=row['no_of_boxes'],
            factory=row['factory'],
            ex_factory_date=row['ex_factory_date'],
            factory_remarks=row['factory_remarks'],
            dispatched_box=row['dispatched_box'],
            dispatched_qty=row['dispatched_qty'],
            balance=row['balance'],
            status=row['status'],
            dispatch_date=row['dispatch_date'],
            transporter=row['transporter'],
            grn_date=row['grn_date'],
            grn_status=row['grn_status'],
            is_revised=bool(row['is_revised']),
        )
        pg_session.merge(po_item)
        migrated_po += 1
    
    pg_session.commit()
    print(f"   ✓ Migrated {migrated_po} po_items records")
    
    if orphaned_eans:
        print(f"\n   ⚠️  Note: {len(orphaned_eans)} EANs in po_items don't exist in style_master")
        print(f"      These EANs were set to NULL to satisfy foreign key constraint")
        print(f"      You can add them to style_master later via the web interface")
    
    # Reset sequences to continue from max ID
    print("\n3. Resetting auto-increment sequences...")
    try:
        # Get max IDs
        max_style_id = pg_session.query(func.max(StyleMaster.id)).scalar() or 0
        max_po_id = pg_session.query(func.max(POItem.id)).scalar() or 0
        
        # Reset sequences
        pg_session.execute(text(f"SELECT setval('style_master_id_seq', {max_style_id}, true);"))
        pg_session.execute(text(f"SELECT setval('po_items_id_seq', {max_po_id}, true);"))
        pg_session.commit()
        print(f"   ✓ Sequences reset (style_master: {max_style_id}, po_items: {max_po_id})")
    except Exception as e:
        print(f"   ⚠️  Could not reset sequences: {e}")
        pg_session.rollback()
    
    print("\n" + "="*50)
    print("✓ Migration completed successfully!")
    print("="*50)
    print(f"\nSummary:")
    print(f"  - style_master: {migrated_master} records")
    print(f"  - po_items: {migrated_po} records")
    print(f"\nDatabase structure:")
    print(f"  - style_master: id (PRIMARY KEY), ean (UNIQUE)")
    print(f"  - po_items: id (PRIMARY KEY), ean (FOREIGN KEY)")
    print(f"\nForeign key relationship:")
    print(f"  po_items.ean → style_master.ean (EAN links the tables)")
    print(f"\nYou can now use JOIN queries:")
    print(f"  SELECT * FROM po_items JOIN style_master ON po_items.ean = style_master.ean")
    
except Exception as e:
    pg_session.rollback()
    print(f"\n✗ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    raise
finally:
    sqlite_po.close()
    sqlite_master.close()
    pg_session.close()

