"""
Script to reset admin password
Usage: python reset_admin_password.py [--username USERNAME] [--password PASSWORD]
"""
import sys
from getpass import getpass
from dotenv import load_dotenv
from database import get_db_session
from models.user import User

load_dotenv()

def reset_password(username=None, password=None):
    """Reset password for an admin user"""
    print("="*70)
    print("Reset Admin Password")
    print("="*70)
    
    if not username:
        username = input("\nEnter username: ").strip()
    
    if not username:
        print("✗ Username is required")
        return False
    
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(username=username).first()
            
            if not user:
                print(f"✗ User '{username}' not found")
                return False
            
            print(f"\nFound user: {user.username}")
            print(f"  Email: {user.email}")
            print(f"  Role: {user.role}")
            
            if not password:
                password = getpass("Enter new password: ")
                confirm_password = getpass("Confirm new password: ")
                
                if password != confirm_password:
                    print("✗ Passwords do not match")
                    return False
                
                if len(password) < 6:
                    print("✗ Password must be at least 6 characters")
                    return False
            
            # Update password
            user.set_password(password)
            session.commit()
            
            print(f"\n✓ Password reset successfully for user '{username}'")
            print("  You can now log in with the new password")
            return True
            
    except Exception as e:
        print(f"\n✗ Error resetting password: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Reset admin password')
    parser.add_argument('--username', '-u', help='Username')
    parser.add_argument('--password', '-p', help='New password (not recommended via CLI)')
    
    args = parser.parse_args()
    
    if args.password:
        print("⚠️  WARNING: Password provided via command line is visible!")
        print("   Consider using interactive mode for better security.\n")
    
    success = reset_password(username=args.username, password=args.password)
    sys.exit(0 if success else 1)


