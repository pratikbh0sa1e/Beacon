"""
Simple script to clear session storage completely
"""
import os
import json
from pathlib import Path

def clear_session_storage():
    """Clear all session storage data"""
    
    session_storage_path = Path("data/web_scraping_sessions")
    
    if not session_storage_path.exists():
        print("❌ Session storage directory not found")
        return
    
    # Files to clear
    files_to_clear = [
        "scraped_documents.json",
        "sources.json",
        "logs.json",
        "counters.json"
    ]
    
    print("🗑️  Clearing session storage files...\n")
    
    for filename in files_to_clear:
        filepath = session_storage_path / filename
        
        if filepath.exists():
            # Backup
            backup_path = session_storage_path / f"{filename}.backup"
            print(f"💾 Backing up: {filename} → {backup_path.name}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Clear file
            if filename == "scraped_documents.json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                print(f"✅ Cleared: {filename} (was {len(data)} items)")
            
            elif filename == "sources.json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"✅ Cleared: {filename} (was {len(data)} items)")
            
            elif filename == "logs.json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump([], f)
                print(f"✅ Cleared: {filename} (was {len(data)} items)")
            
            elif filename == "counters.json":
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({"source_id": 1, "log_id": 1}, f)
                print(f"✅ Reset: {filename}")
        else:
            print(f"⏭️  Skipped: {filename} (not found)")
    
    print(f"\n✅ Session storage cleared!")
    print(f"   Backups saved in: {session_storage_path}")
    print(f"\n⚠️  Note: This only clears the session cache.")
    print(f"   Database documents are NOT affected.")


if __name__ == "__main__":
    print("=" * 60)
    print("CLEAR SESSION STORAGE")
    print("=" * 60)
    print("\nThis will clear the session storage cache (3258 documents).")
    print("Database documents will NOT be affected.\n")
    print("Backups will be created before clearing.\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        clear_session_storage()
    else:
        print("❌ Operation cancelled")
