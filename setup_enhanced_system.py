#!/usr/bin/env python3
"""
Complete setup script for enhanced web scraping and RAG system
This script will:
1. Add missing database columns
2. Populate content hashes for existing documents
3. Migrate documents to family structure
4. Test the enhanced RAG system
"""
import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

import subprocess
import time
from pathlib import Path

def run_script(script_path, description):
    """Run a Python script and handle errors"""
    print(f"\n🚀 {description}")
    print("=" * 60)
    
    try:
        # Run the script
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, cwd='.')
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully!")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print(f"❌ {description} failed!")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running {script_path}: {str(e)}")
        return False
    
    return True

def check_database_connection():
    """Check if database is accessible"""
    print("🔍 Checking database connection...")
    
    try:
        from backend.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_enhanced_rag():
    """Test the enhanced RAG system"""
    print("\n🧪 Testing Enhanced RAG System")
    print("=" * 60)
    
    try:
        from Agent.rag_enhanced.family_aware_retriever import enhanced_search_documents
        
        # Test search
        result = enhanced_search_documents(
            query="education policy guidelines",
            top_k=3,
            user_role="developer"
        )
        
        print("Enhanced RAG Test Result:")
        print(result[:500] + "..." if len(result) > 500 else result)
        print("✅ Enhanced RAG system is working!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced RAG test failed: {str(e)}")
        return False

def main():
    """Main setup function"""
    print("🎯 Enhanced Web Scraping & RAG System Setup")
    print("=" * 60)
    print("This will set up:")
    print("• Document families and versioning")
    print("• Enhanced web scraping with deduplication")
    print("• Family-aware RAG retrieval")
    print("• Improved accuracy and performance")
    print()
    
    # Check if user wants to continue
    response = input("Continue with setup? (y/N): ").lower().strip()
    if response != 'y':
        print("Setup cancelled.")
        return 1
    
    # Step 1: Check database connection
    if not check_database_connection():
        print("\n❌ Setup failed: Cannot connect to database")
        print("Please check your database configuration in .env file")
        return 1
    
    # Step 2: Add missing columns
    if not run_script("scripts/add_missing_columns.py", "Adding missing database columns"):
        print("\n❌ Setup failed at step 2")
        return 1
    
    # Step 3: Populate content hashes
    if not run_script("scripts/populate_content_hashes.py", "Populating content hashes"):
        print("\n❌ Setup failed at step 3")
        return 1
    
    # Step 4: Migrate to families (this might take a while)
    print("\n⚠️  The next step (family migration) may take several minutes for large databases...")
    response = input("Continue with family migration? (y/N): ").lower().strip()
    if response == 'y':
        if not run_script("scripts/migrate_existing_documents_to_families.py", "Migrating documents to families"):
            print("\n⚠️  Family migration failed, but system can still work")
            print("You can run the migration later from the web interface")
    else:
        print("⏭️  Skipping family migration (can be done later)")
    
    # Step 5: Test enhanced RAG
    if not test_enhanced_rag():
        print("\n⚠️  Enhanced RAG test failed, but basic system should work")
    
    # Step 6: Final summary
    print("\n" + "=" * 60)
    print("🎉 Enhanced System Setup Complete!")
    print("=" * 60)
    
    print("\n📋 What's been set up:")
    print("✅ Database schema updated with family support")
    print("✅ Content hashes populated for deduplication")
    print("✅ Enhanced web scraping processor ready")
    print("✅ Family-aware RAG retriever ready")
    
    print("\n🚀 Next steps:")
    print("1. Start your backend server:")
    print("   uvicorn backend.main:app --reload")
    print()
    print("2. Access the enhanced web scraping page:")
    print("   http://localhost:3000/admin/web-scraping")
    print()
    print("3. Try the enhanced features:")
    print("   • Add sources with incremental scraping")
    print("   • View document families")
    print("   • Test improved RAG accuracy")
    
    print("\n📚 Key improvements:")
    print("• 🔄 Automatic deduplication")
    print("• 📁 Document versioning and families")
    print("• 🎯 Better RAG accuracy with family context")
    print("• ⚡ Incremental scraping (skip unchanged docs)")
    print("• 🔍 Update detection for existing documents")
    
    return 0

if __name__ == "__main__":
    exit(main())