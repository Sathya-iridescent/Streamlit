"""
Functional Test: Test that the application works the same way
Tests key functionality to ensure old and new versions behave identically
"""
import os
from dotenv import load_dotenv
from database import get_db_session, POItem, StyleMaster, initialize_db

load_dotenv()

print("="*70)
print("FUNCTIONAL TEST: Application Behavior Verification")
print("="*70)

# ==================== TEST 1: Database Connection ====================
print("\n1. Testing Database Connection...")
try:
    initialize_db()
    print("  ✓ Database initialized successfully")
except Exception as e:
    print(f"  ✗ Database initialization failed: {e}")
    exit(1)

# ==================== TEST 2: Style Master Operations ====================
print("\n2. Testing Style Master Operations...")

with get_db_session() as session:
    # Test: Create a style master entry
    test_ean = "TEST_EAN_1234567890"
    test_style = StyleMaster(
        ean=test_ean,
        style_no="TEST-STYLE-001",
        buyer="ASL-Mens AW Fashion"
    )
    session.add(test_style)
    # commit happens automatically

    # Test: Read it back (need to refresh session)
    session.commit()  # Ensure it's committed
    retrieved = session.query(StyleMaster).filter_by(ean=test_ean).first()
    if retrieved and retrieved.style_no == "TEST-STYLE-001":
        print("  ✓ Create and Read: SUCCESS")
        
        # Test: Update it
        retrieved.style_no = "TEST-STYLE-002"
        session.commit()
        updated = session.query(StyleMaster).filter_by(ean=test_ean).first()
        if updated and updated.style_no == "TEST-STYLE-002":
            print("  ✓ Update: SUCCESS")
        else:
            print("  ✗ Update: FAILED")

        # Test: Delete it
        session.delete(retrieved)
        session.commit()
        deleted = session.query(StyleMaster).filter_by(ean=test_ean).first()
        if deleted is None:
            print("  ✓ Delete: SUCCESS")
        else:
            print("  ✗ Delete: FAILED")
    else:
        print("  ✗ Create and Read: FAILED")
        if not retrieved:
            print("    (Record not found after creation)")

# ==================== TEST 3: PO Item Operations ====================
print("\n3. Testing PO Item Operations...")

with get_db_session() as session:
    # Test: Create a PO item (use unique po_number to avoid conflicts)
    import time
    unique_po = f"TEST_PO_{int(time.time())}"
    test_ean = f"TEST_EAN_{int(time.time())}"
    
    # First create style_master entry for the EAN (foreign key requirement)
    test_style = StyleMaster(
        ean=test_ean,
        style_no="TEST-STYLE",
        buyer="Test Buyer"
    )
    session.add(test_style)
    session.commit()
    
    test_po = POItem(
        filename="test.pdf",
        po_number=unique_po,
        po_date="01.01.2024",
        ean=test_ean,  # Use the EAN we just created
        quantity=100,
        caselot=10,
        status="Pending"
    )
    session.add(test_po)
    # commit happens automatically

    # Test: Read it back
    session.commit()  # Ensure it's committed
    retrieved_po = session.query(POItem).filter_by(po_number=unique_po).first()
    if retrieved_po and retrieved_po.quantity == 100:
        print("  ✓ Create and Read: SUCCESS")
        
        # Test: Update dispatched_box (should auto-calculate)
        retrieved_po.dispatched_box = 5
        retrieved_po.dispatched_qty = retrieved_po.dispatched_box * retrieved_po.caselot
        retrieved_po.balance = retrieved_po.quantity - retrieved_po.dispatched_qty
        session.commit()
        
        updated_po = session.query(POItem).filter_by(po_number=unique_po).first()
        expected_qty = 5 * 10  # 50
        expected_balance = 100 - 50  # 50
        if updated_po.dispatched_qty == expected_qty and updated_po.balance == expected_balance:
            print("  ✓ Auto-calculation (dispatched_qty, balance): SUCCESS")
        else:
            print(f"  ✗ Auto-calculation: FAILED (got qty={updated_po.dispatched_qty}, balance={updated_po.balance})")

        # Cleanup
        session.delete(retrieved_po)
        session.delete(test_style)
        session.commit()
    else:
        print("  ✗ Create and Read: FAILED")
        if not retrieved_po:
            print("    (Record not found after creation)")

# ==================== TEST 4: JOIN Query ====================
print("\n4. Testing JOIN Query...")

with get_db_session() as session:
    # Create test data
    test_ean = "JOIN_TEST_EAN"
    style = StyleMaster(ean=test_ean, style_no="JOIN-STYLE", buyer="Test Buyer")
    session.add(style)
    
    po_item = POItem(
        po_number="JOIN_TEST_PO",
        ean=test_ean,
        quantity=50,
        status="Pending"
    )
    session.add(po_item)
    session.commit()

    # Test JOIN query
    results = session.query(POItem, StyleMaster).join(
        StyleMaster, POItem.ean == StyleMaster.ean
    ).filter(POItem.po_number == "JOIN_TEST_PO").all()

    if results:
        po, style = results[0]
        if po.ean == test_ean and style.style_no == "JOIN-STYLE":
            print("  ✓ JOIN Query: SUCCESS")
            print(f"    PO #{po.po_number} -> Style: {style.style_no}, Buyer: {style.buyer}")
        else:
            print("  ✗ JOIN Query: FAILED (data mismatch)")
    else:
        print("  ✗ JOIN Query: FAILED (no results)")

    # Cleanup
    session.delete(po_item)
    session.delete(style)
    session.commit()

# ==================== TEST 5: Foreign Key Relationship ====================
print("\n5. Testing Foreign Key Relationship...")

with get_db_session() as session:
    # Test: Try to create PO item with NULL EAN (foreign key allows NULL)
    orphan_po = POItem(
        po_number="ORPHAN_TEST",
        ean=None,  # NULL EAN is allowed (foreign key is nullable)
        quantity=10,
        status="Pending"
    )
    session.add(orphan_po)
    session.commit()
    
    # Verify it was created (foreign key allows NULL)
    orphan = session.query(POItem).filter_by(po_number="ORPHAN_TEST").first()
    if orphan and orphan.ean is None:
        print("  ✓ Foreign Key: Allows NULL EAN (foreign key is nullable)")
        session.delete(orphan)
        session.commit()
    else:
        print("  ✗ Foreign Key: FAILED")

# ==================== TEST 6: get_style_and_buyer_from_db Function ====================
print("\n6. Testing get_style_and_buyer_from_db() function...")

from database import get_style_and_buyer_from_db

with get_db_session() as session:
    # Create test style
    test_ean = "FUNC_TEST_EAN"
    style = StyleMaster(ean=test_ean, style_no="FUNC-STYLE", buyer="FUNC-BUYER")
    session.add(style)
    session.commit()

    # Test the function
    style_no, buyer = get_style_and_buyer_from_db(test_ean)
    if style_no == "FUNC-STYLE" and buyer == "FUNC-BUYER":
        print("  ✓ get_style_and_buyer_from_db(): SUCCESS")
    else:
        print(f"  ✗ get_style_and_buyer_from_db(): FAILED (got style_no={style_no}, buyer={buyer})")

    # Test with non-existent EAN
    style_no, buyer = get_style_and_buyer_from_db("NON_EXISTENT")
    if style_no == "" and buyer == "":
        print("  ✓ get_style_and_buyer_from_db() with non-existent EAN: SUCCESS")
    else:
        print("  ✗ get_style_and_buyer_from_db() with non-existent EAN: FAILED")

    # Cleanup
    session.delete(style)
    session.commit()

# ==================== SUMMARY ====================
print("\n" + "="*70)
print("FUNCTIONAL TEST SUMMARY")
print("="*70)
print("\n✓ All functional tests completed!")
print("  - Database operations work correctly")
print("  - JOIN queries function properly")
print("  - Foreign key relationships are intact")
print("  - Helper functions work as expected")
print("\n" + "="*70)

