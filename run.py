#!/usr/bin/env python3
"""
Simple script to run JobHunter directly
"""
import os
import sys

# Add the project directory to the Python path
# This ensures imports in the project work correctly
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import traceback
from datetime import datetime

def check_environment():
    """Check if the environment is properly set up."""
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your email credentials and OpenAI API key.")
        return False
    
    # Check if required packages are installed
    required_packages = [
        'pandas', 'requests', 'beautifulsoup4', 'selenium', 
        'python-dotenv', 'openai'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def run_job_hunter():
    """Run the JobHunter directly."""
    if not check_environment():
        sys.exit(1)
    
    print("=" * 70)
    print(f"🚀 Running JobHunter on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
    print("🔍 Searching for jobs posted in the last 7 days in Bangalore")
    print("=" * 70)
    
    try:
        # Import and run enhanced_main directly instead of using subprocess
        # This ensures proper module resolution
        import enhanced_main
        enhanced_main.main()
        
        print("=" * 70)
        print("✅ JobHunter completed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Error running JobHunter: {e}")
        traceback.print_exc()  # Print full traceback for better debugging
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 JobHunter interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    run_job_hunter()