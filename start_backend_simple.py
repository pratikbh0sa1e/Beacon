#!/usr/bin/env python3
"""
Simple backend starter
"""
import subprocess
import sys
import os

def start_backend():
    """Start the backend server"""
    try:
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start uvicorn
        cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        
        print("🚀 Starting backend server...")
        print(f"Command: {' '.join(cmd)}")
        
        # Start the process
        process = subprocess.Popen(cmd)
        
        print(f"✅ Backend started with PID: {process.pid}")
        print("🌐 Backend should be available at: http://localhost:8000")
        print("📚 API docs at: http://localhost:8000/docs")
        
        # Wait for the process
        process.wait()
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")

if __name__ == "__main__":
    start_backend()