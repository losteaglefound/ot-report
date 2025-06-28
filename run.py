#!/usr/bin/env python3
"""
OT Report Generator - Startup Script
Run this script to start the FastAPI application
"""

import uvicorn
import os
import sys

def main():
    """Start the FastAPI application"""
    
    # Ensure we're in the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🏥 Starting OT Report Generator...")
    print("📋 Automated Bayley-4 to OT Report Generation")
    print("-" * 50)
    
    try:
        # Start the FastAPI application
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n✅ Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 