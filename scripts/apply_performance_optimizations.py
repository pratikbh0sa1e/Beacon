#!/usr/bin/env python3
"""
Quick setup script to apply performance optimizations
Run this after pulling the performance optimization changes
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║   🚀 BEACON Performance Optimization Setup                ║
    ║   This will apply all performance improvements             ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if we're in the right directory
    if not os.path.exists("backend/main.py"):
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    steps_completed = 0
    total_steps = 3
    
    # Step 1: Install dependencies
    if run_command(
        "pip install fastapi-cache2==0.2.2",
        "Step 1/3: Installing caching dependency"
    ):
        steps_completed += 1
    
    # Step 2: Run database migrations
    if run_command(
        "alembic upgrade head",
        "Step 2/3: Applying database indexes"
    ):
        steps_completed += 1
    else:
        print("\n⚠️  Migration failed. You may need to run it manually:")
        print("   alembic upgrade head")
    
    # Step 3: Verify setup
    print(f"\n{'='*60}")
    print("🔍 Step 3/3: Verifying setup")
    print(f"{'='*60}")
    
    # Check if cache is installed
    try:
        import fastapi_cache
        print("✅ fastapi-cache2 installed successfully")
        steps_completed += 1
    except ImportError:
        print("⚠️  fastapi-cache2 not found. Run: pip install fastapi-cache2")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 Setup Summary: {steps_completed}/{total_steps} steps completed")
    print(f"{'='*60}")
    
    if steps_completed == total_steps:
        print("""
    ✅ All optimizations applied successfully!
    
    🎯 Next Steps:
    1. Restart your backend server:
       uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
    
    2. Check startup logs for:
       ✅ Cache initialized (in-memory)
       ✅ Sync scheduler started
       🎉 BEACON Platform ready!
    
    3. Test performance:
       - Initial load should be 0.5-1s (down from 4-5s)
       - Cached loads should be 0.1-0.3s
       - Check X-Process-Time header in responses
    
    📖 For more details, see: PERFORMANCE_OPTIMIZATIONS.md
        """)
    else:
        print("""
    ⚠️  Some steps failed. Please check the errors above.
    
    Manual steps:
    1. Install cache: pip install fastapi-cache2
    2. Run migration: alembic upgrade head
    3. Restart backend
    
    📖 See PERFORMANCE_OPTIMIZATIONS.md for troubleshooting
        """)
    
    return 0 if steps_completed == total_steps else 1

if __name__ == "__main__":
    sys.exit(main())
