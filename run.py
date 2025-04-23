#!/usr/bin/env python3
"""
Simple script to run JobHunter directly
"""
import os
import sys
import subprocess
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
    
    print("=" * 50)
    print(f"🚀 Running JobHunter on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Use the enhanced main script
        subprocess.check_call([sys.executable, 'enhanced_main.py'])
        print("=" * 50)
        print("✅ JobHunter completed successfully!")
        print("=" * 50)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running JobHunter: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 JobHunter interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    run_job_hunter()