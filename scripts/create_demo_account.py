#!/usr/bin/env python3
"""
Create Demo Account Script

This script creates a demo account for testing purposes.
Can be run standalone or as part of deployment.

Usage:
    python scripts/create_demo_account.py
    
Demo Account Details:
- Email: demo@beacon.system
- Password: demo123
- Role: student
- Pre-approved and verified
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.init_developer import initialize_demo_account

def main():
    """Main function to create demo account"""
    print("🎯 Creating Demo Account...")
    print("-" * 50)
    
    try:
        initialize_demo_account()
        print("✅ Demo account setup complete!")
        
        print("\n📋 Demo Account Information:")
        print("   Email: demo@beacon.system")
        print("   Password: demo123")
        print("   Role: Student")
        print("   Status: Pre-approved & verified")
        
        print("\n🔗 You can now use this account to:")
        print("   • Test the login functionality")
        print("   • Browse documents (student permissions)")
        print("   • Use the AI chat feature")
        print("   • Test mobile responsiveness")
        
        print("\n⚠️  Security Note:")
        print("   This is a demo account with a simple password.")
        print("   Do not use in production without changing credentials.")
        
    except Exception as e:
        print(f"❌ Error creating demo account: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()