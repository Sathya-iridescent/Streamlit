"""
Script to change a user's role (make user admin or change admin to user)
Usage: python change_user_role.py --username USERNAME --role admin
       python change_user_role.py --username USERNAME --role user
"""
import os
import sys
import argparse
from dotenv import load_dotenv
from database import initialize_db, get_db_session
from models.user import User

# Load environment variables
load_dotenv()

def change_user_role(username=None, role=None):
    """
    Change a user's role
    
    Args:
        username: Username of the user to modify
        role: New role ('admin' or 'user')
    """
    print("="*70)
    print("Change User Role")
    print("="*70)
    
    # Initialize database to ensure tables exist
    print("\n1. Initializing database...")
    initialize_db()
    print("   ✓ Database initialized")
    
    # Get user input if not provided
    if not username:
        username = input("\nEnter username: ").strip()
    if not username:
        print("✗ Username is required")
        return False
    
    if not role:
        role = input("Enter new role (admin/user): ").strip().lower()
    if not role:
        print("✗ Role is required")
        return False
    
    if role not in ['admin', 'user']:
        print("✗ Role must be 'admin' or 'user'")
        return False
    
    # Find and update user
    print(f"\n2. Finding user '{username}'...")
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(username=username).first()
            
            if not user:
                print(f"✗ User '{username}' not found")
                return False
            
            old_role = user.role
            user.role = role
            session.commit()
            
            print(f"\n✓ User role changed successfully!")
            print("="*70)
            print("User Details:")
            print("="*70)
            print(f"  Username: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Old Role: {old_role}")
            print(f"  New Role: {user.role}")
            print(f"  Active: {user.is_active}")
            print(f"  Verified: {user.is_verified}")
            print("="*70)
            return True
            
    except Exception as e:
        print(f"\n✗ Error changing user role: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description='Change a user\'s role in PO Extract',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (will prompt for all fields)
  python change_user_role.py
  
  # Command-line mode - Make user admin
  python change_user_role.py --username john --role admin
  
  # Command-line mode - Change admin to user
  python change_user_role.py --username admin --role user
        """
    )
    
    parser.add_argument('--username', '-u', help='Username of the user to modify')
    parser.add_argument('--role', '-r', choices=['admin', 'user'], help='New role (admin or user)')
    
    args = parser.parse_args()
    
    success = change_user_role(
        username=args.username,
        role=args.role
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

