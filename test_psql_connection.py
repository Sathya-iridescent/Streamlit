"""
Step 1: Test PostgreSQL Connectivity
This script tests if we can connect to PostgreSQL
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

print("="*70)
print("STEP 1: Testing PostgreSQL Connectivity")
print("="*70)

# Get connection details
DB_TYPE = os.getenv('DB_TYPE', 'postgresql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'poextract_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

print(f"\nConnection Details:")
print(f"  Type: {DB_TYPE}")
print(f"  Host: {DB_HOST}")
print(f"  Port: {DB_PORT}")
print(f"  Database: {DB_NAME}")
print(f"  User: {DB_USER}")
print(f"  Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else '(not set)'}")

if DB_TYPE != 'postgresql':
    print(f"\n⚠️  WARNING: DB_TYPE is '{DB_TYPE}', not 'postgresql'")
    print("   Set DB_TYPE=postgresql in .env file")
    exit(1)

if not DB_PASSWORD:
    print(f"\n⚠️  WARNING: DB_PASSWORD is not set in .env file")
    print("   Please set DB_PASSWORD in .env file")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"\nAttempting to connect...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"✓ Connection successful!")
        print(f"\nPostgreSQL Version:")
        print(f"  {version}")
        
        # Test if database exists
        result = conn.execute(text("SELECT current_database();"))
        db_name = result.fetchone()[0]
        print(f"\n✓ Connected to database: {db_name}")
        
        # Check if tables exist
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if tables:
            print(f"\n✓ Existing tables: {', '.join(tables)}")
        else:
            print(f"\n✓ Database is empty (no tables yet) - This is expected before migration")
        
        print(f"\n{'='*70}")
        print("✓ PostgreSQL connectivity test PASSED")
        print("  Ready to proceed to Step 2: Test App with PostgreSQL")
        print(f"{'='*70}")
        
except Exception as e:
    print(f"\n✗ Connection FAILED: {e}")
    print(f"\nTroubleshooting:")
    print(f"  1. Check if PostgreSQL is running:")
    print(f"     brew services list | grep postgresql")
    print(f"  2. Start PostgreSQL if needed:")
    print(f"     brew services start postgresql@15")
    print(f"  3. Verify database exists:")
    print(f"     createdb {DB_NAME}")
    print(f"  4. Check credentials in .env file")
    exit(1)




