"""
Production Database Module - PostgreSQL with SQLAlchemy
Single database with two tables connected by foreign key (EAN)
"""
import os
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

# Load environment variables from .env file
load_dotenv()

Base = declarative_base()

# ==================== CONFIGURATION ====================
# 1. Check Streamlit Secrets (Cloud), then Environment Variables (Local)
DATABASE_URL = st.secrets.get("DATABASE_URL") or os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Render/Heroku/Supabase fix: SQLAlchemy needs 'postgresql://'
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    DB_TYPE = 'postgresql'
else:
    # Local fallback to SQLite if no production DB is found
    DB_TYPE = 'sqlite'
    DATABASE_URL = "sqlite:///poextract.db"
    print("⚠️ No DATABASE_URL found. Falling back to local SQLite.")


# ==================== ENGINE & SESSION ====================
# Determine DB_TYPE from DATABASE_URL if not explicitly set
if not DATABASE_URL or DATABASE_URL.startswith('sqlite'):
    db_type_for_engine = 'sqlite'
else:
    db_type_for_engine = 'postgresql'

if db_type_for_engine == 'postgresql':
    engine = create_engine(
        DATABASE_URL,
        # IMPORTANT: Most cloud DBs require SSL to connect from Streamlit
        connect_args={"sslmode": "require"}, 
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
else:
    # SQLite doesn't need connection pooling
    engine = create_engine(
        DATABASE_URL,
        echo=False
    )

SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))

# ==================== MODELS ====================
# Models are now defined in the models/ directory:
# - models/user.py - User model
# - models/po_item.py - POItem model  
# - models/style_master.py - StyleMaster model
# Import them to ensure they're registered with Base before initialize_db() is called

# ==================== HELPER FUNCTIONS ====================

@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db():
    """Get database session (for Flask integration)"""
    return SessionLocal()


# ==================== BACKWARD COMPATIBILITY ====================
# These functions maintain compatibility with existing app.py code

def get_po_db_connection():
    """
    Backward compatibility function.
    Returns a session instead of raw connection.
    """
    return get_db()


def get_master_db_connection():
    """
    Backward compatibility function.
    Returns a session instead of raw connection.
    Same as get_po_db_connection() since we use one database now.
    """
    return get_db()


def get_style_and_buyer_from_db(ean: str):
    """
    Returns (style_no, buyer) from style_master for a given EAN.
    Uses JOIN query for efficiency.
    """
    from models.style_master import StyleMaster
    with get_db_session() as session:
        style = session.query(StyleMaster).filter_by(ean=ean).first()
        if style:
            return (style.style_no or "", style.buyer or "")
        return "", ""


def initialize_db():
    """Create all tables if they don't exist"""
    # Import all models to ensure they're registered with Base
    from models.user import User
    from models.po_item import POItem
    from models.style_master import StyleMaster
    
    try:
        # Create all tables (users, po_items, style_master)
        Base.metadata.create_all(bind=engine)
        
        if DATABASE_URL and not DATABASE_URL.startswith('sqlite'):
            print(f"✓ Database initialized: PostgreSQL")
        else:
            print(f"✓ Database initialized: SQLite (fallback)")
            
    except Exception as e:
        # This will show the actual error message in your app UI
        st.error(f"Actual Connection Error: {str(e)}")
        raise e
    
    if DATABASE_URL and not DATABASE_URL.startswith('sqlite'):
        # PostgreSQL (from DATABASE_URL or individual components)
        print(f"✓ Database initialized: PostgreSQL")
        print(f"  Tables: users, po_items, style_master")
    else:
        print(f"✓ Database initialized: SQLite (fallback)")
        print(f"  Tables: users, po_items, style_master")


# ==================== EXAMPLE USAGE ====================
if __name__ == "__main__":
    # Initialize database
    initialize_db()
    print("\n✓ Tables created:")
    print("  - style_master: id (PRIMARY KEY), ean (UNIQUE)")
    print("  - po_items: id (PRIMARY KEY), ean (FOREIGN KEY -> style_master.ean)")
    print("\n✓ Foreign key relationship established:")
    print("  po_items.ean -> style_master.ean (EAN links the tables)")





