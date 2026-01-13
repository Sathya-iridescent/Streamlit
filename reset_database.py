"""
Reset Database Script
Drops all tables and recreates them (fresh start for testing)
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from database import Base, initialize_db, DB_TYPE, DATABASE_URL

load_dotenv()

print("="*70)
print("DATABASE RESET SCRIPT")
print("="*70)

if DB_TYPE == 'postgresql':
    print(f"\n⚠️  WARNING: This will DROP ALL TABLES in PostgreSQL database!")
    print(f"   Database: {os.getenv('DB_NAME', 'poextract_db')}")
    print(f"   Tables to be dropped: po_items, style_master")
    print(f"\n   All data will be permanently deleted!")
else:
    print(f"\n⚠️  WARNING: This will DELETE SQLite database file!")
    print(f"   File: poextract.db")

response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()

if response != 'yes':
    print("\n✗ Reset cancelled.")
    exit(0)

print("\n" + "="*70)
print("Resetting database...")
print("="*70)

try:
    if DB_TYPE == 'postgresql':
        # PostgreSQL: Drop tables
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Drop tables in correct order (respecting foreign keys)
            print("\n1. Dropping tables...")
            conn.execute(text("DROP TABLE IF EXISTS po_items CASCADE;"))
            print("   ✓ Dropped po_items table")
            
            conn.execute(text("DROP TABLE IF EXISTS style_master CASCADE;"))
            print("   ✓ Dropped style_master table")
            
            conn.commit()
        
        # Recreate tables
        print("\n2. Recreating tables...")
        initialize_db()
        print("   ✓ Tables recreated")
        
    else:
        # SQLite: Delete database file
        db_file = "poextract.db"
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"\n1. Deleted SQLite database: {db_file}")
        
        # Recreate tables
        print("\n2. Recreating tables...")
        initialize_db()
        print("   ✓ Tables recreated")
    
    print("\n" + "="*70)
    print("✓ Database reset completed successfully!")
    print("="*70)
    print("\nDatabase is now empty and ready for testing.")
    print("You can now:")
    print("  1. Upload PDFs via the web interface")
    print("  2. Add entries to style_master")
    print("  3. Test all functionality from scratch")
    print("")
    
except Exception as e:
    print(f"\n✗ Reset failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)




