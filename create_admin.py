"""
Script to create an admin account with all privileges
Usage: python create_admin.py [--username USERNAME] [--email EMAIL] [--password PASSWORD]
"""
import os
import sys
import argparse
from getpass import getpass
from dotenv import load_dotenv
from database import initialize_db, get_db_session
from models.user import User

# Load environment variables
load_dotenv()

def create_admin(username=None, email=None, password=None, full_name=None):
    """
    Create an admin user account
    
    Args:
        username: Admin username (required)
        email: Admin email (required)
        password: Admin password (required)
        full_name: Full name (optional)
    """
    print("="*70)
    print("Create Admin Account")
    print("="*70)
    
    # Initialize database to ensure tables exist
    print("\n1. Initializing database...")
    initialize_db()
    print("   ✓ Database initialized")
    
    # Get user input if not provided
    if not username:
        username = input("\nEnter admin username: ").strip()
    if not username:
        print("✗ Username is required")
        return False
    
    if not email:
        email = input("Enter admin email: ").strip()
    if not email:
        print("✗ Email is required")
        return False
    
    if not password:
        password = getpass("Enter admin password: ")
        confirm_password = getpass("Confirm admin password: ")
        if password != confirm_password:
            print("✗ Passwords do not match")
            return False
        if len(password) < 6:
            print("✗ Password must be at least 6 characters")
            return False
    
    if not full_name:
        full_name = input("Enter full name (optional): ").strip() or None
    
    # Check if user already exists
    print("\n2. Checking for existing user...")
    try:
        with get_db_session() as session:
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                if existing_user.username == username:
                    print(f"   ⚠️  Username '{username}' already exists")
                else:
                    print(f"   ⚠️  Email '{email}' already exists")
                
                response = input("   Do you want to update this user to admin? (y/n): ").strip().lower()
                if response == 'y':
                    # Update existing user to admin
                    existing_user.set_password(password)
                    existing_user.role = 'admin'
                    existing_user.is_active = True
                    existing_user.is_verified = True
                    if full_name:
                        existing_user.full_name = full_name
                    session.commit()
                    print(f"\n✓ User '{username}' updated to admin successfully!")
                    print(f"   Role: {existing_user.role}")
                    print(f"   Active: {existing_user.is_active}")
                    print(f"   Verified: {existing_user.is_verified}")
                    return True
                else:
                    print("   Operation cancelled")
                    return False
            
            # Create new admin user
            print("   ✓ No existing user found, creating new admin...")
            
            admin_user = User(
                username=username,
                email=email,
                full_name=full_name,
                role='admin',
                is_active=True,
                is_verified=True
            )
            admin_user.set_password(password)
            
            session.add(admin_user)
            session.commit()
            
            print(f"\n✓ Admin account created successfully!")
            print("="*70)
            print("Admin Account Details:")
            print("="*70)
            print(f"  Username: {admin_user.username}")
            print(f"  Email: {admin_user.email}")
            print(f"  Full Name: {admin_user.full_name or 'Not set'}")
            print(f"  Role: {admin_user.role}")
            print(f"  Active: {admin_user.is_active}")
            print(f"  Verified: {admin_user.is_verified}")
            print(f"  User ID: {admin_user.id}")
            print("="*70)
            print("\n✓ You can now log in with these credentials at /auth/login")
            return True
            
    except Exception as e:
        print(f"\n✗ Error creating admin account: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Create an admin account for PO Extract',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (will prompt for all fields)
  python create_admin.py
  
  # Command-line mode
  python create_admin.py --username admin --email admin@example.com --password mypassword
  
  # With full name
  python create_admin.py --username admin --email admin@example.com --password mypassword --full-name "Admin User"
        """
    )
    
    parser.add_argument('--username', '-u', help='Admin username')
    parser.add_argument('--email', '-e', help='Admin email')
    parser.add_argument('--password', '-p', help='Admin password (not recommended, use interactive mode)')
    parser.add_argument('--full-name', '-n', help='Full name')
    
    args = parser.parse_args()
    
    # If password is provided via command line, warn user
    if args.password:
        print("⚠️  WARNING: Password provided via command line is visible in process list!")
        print("   Consider using interactive mode for better security.\n")
    
    success = create_admin(
        username=args.username,
        email=args.email,
        password=args.password,
        full_name=args.full_name
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


