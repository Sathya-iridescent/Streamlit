"""
Complete Database Drop Script
Drops the entire PostgreSQL database and recreates it (nuclear option)
Use this if you want to completely start fresh
"""
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'poextract_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

print("="*70)
print("COMPLETE DATABASE DROP SCRIPT")
print("="*70)
print(f"\n⚠️  NUCLEAR OPTION: This will DROP THE ENTIRE DATABASE!")
print(f"   Database: {DB_NAME}")
print(f"   Host: {DB_HOST}:{DB_PORT}")
print(f"\n   ALL DATA WILL BE PERMANENTLY DELETED!")
print(f"   The database will be recreated as empty.")

response = input("\nType 'DROP DATABASE' to confirm: ").strip()

if response != 'DROP DATABASE':
    print("\n✗ Operation cancelled.")
    exit(0)

try:
    # Connect to postgres database (not the target database)
    print(f"\n1. Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database='postgres'  # Connect to default postgres DB
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Terminate all connections to the target database
    print(f"2. Terminating active connections to {DB_NAME}...")
    cur.execute(f"""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '{DB_NAME}'
        AND pid <> pg_backend_pid();
    """)
    print("   ✓ Connections terminated")
    
    # Drop the database
    print(f"3. Dropping database {DB_NAME}...")
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    print("   ✓ Database dropped")
    
    # Recreate the database
    print(f"4. Creating fresh database {DB_NAME}...")
    cur.execute(f"CREATE DATABASE {DB_NAME};")
    print("   ✓ Database created")
    
    cur.close()
    conn.close()
    
    # Initialize tables
    print(f"\n5. Initializing tables...")
    from database import initialize_db
    initialize_db()
    print("   ✓ Tables created")
    
    print("\n" + "="*70)
    print("✓ Complete database reset successful!")
    print("="*70)
    print(f"\nFresh database '{DB_NAME}' is ready for testing.")
    print("")
    
except Exception as e:
    print(f"\n✗ Operation failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)




