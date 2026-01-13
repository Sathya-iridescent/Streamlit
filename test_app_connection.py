"""
Step 2: Test App Connection to PostgreSQL
This script tests if the app can connect and initialize tables
"""
import os
from dotenv import load_dotenv
from database import initialize_db, get_db_session
from models.style_master import StyleMaster
from models.po_item import POItem

load_dotenv()

print("="*70)
print("STEP 2: Testing App Connection to PostgreSQL")
print("="*70)

print("\n1. Initializing database (creating tables if they don't exist)...")
try:
    initialize_db()
    print("  ✓ Database initialized successfully")
except Exception as e:
    print(f"  ✗ Database initialization failed: {e}")
    exit(1)

print("\n2. Testing database session...")
try:
    with get_db_session() as session:
        # Test: Count records (should work even if empty)
        style_count = session.query(StyleMaster).count()
        po_count = session.query(POItem).count()
        
        print(f"  ✓ Session works correctly")
        print(f"    style_master records: {style_count}")
        print(f"    po_items records: {po_count}")
        
        # Test: Create a test record
        print("\n3. Testing write operation...")
        test_style = StyleMaster(
            ean="TEST_CONNECTION_EAN",
            style_no="TEST-STYLE",
            buyer="Test Buyer"
        )
        session.add(test_style)
        # commit happens automatically via context manager
        
        # Test: Read it back
        retrieved = session.query(StyleMaster).filter_by(ean="TEST_CONNECTION_EAN").first()
        if retrieved:
            print(f"  ✓ Write and Read: SUCCESS")
            
            # Cleanup
            session.delete(retrieved)
            session.commit()
            print(f"  ✓ Delete: SUCCESS")
        else:
            print(f"  ✗ Write/Read: FAILED")
            
except Exception as e:
    print(f"  ✗ Session test failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print(f"\n{'='*70}")
print("✓ App connection test PASSED")
print("  Database is ready for migration")
print(f"{'='*70}")




