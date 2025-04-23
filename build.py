"""
Simplified build script for Mac M2 - direct approach without spec file
"""
import os
import sys
import subprocess
import platform
import shutil

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return False
    
    # Check PyInstaller
    try:
        import PyInstaller
        print("✅ PyInstaller is installed")
    except ImportError:
        print("❌ PyInstaller is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    return True

def build_app():
    """Build the executable using PyInstaller - direct approach."""
    print("🔨 Building the app...")
    
    # Run PyInstaller directly with command line arguments
    try:
        cmd = [
            'pyinstaller',
            '--clean',
            '--onedir',  # Use onedir for Mac M2 compatibility
            '--name=JobHunter',
            # Add data files
            '--add-data=.env:.',
            '--add-data=config:config',
            '--add-data=scrapers:scrapers',
            '--add-data=alert:alert',
            '--add-data=utils:utils',
            '--add-data=openai_scraper.py:.',
            # Add imports
            '--hidden-import=openai',
            '--hidden-import=pandas',
            '--hidden-import=numpy',
            '--hidden-import=requests',
            '--hidden-import=bs4',
            '--hidden-import=dotenv',
            '--hidden-import=email.mime.multipart',
            '--hidden-import=email.mime.text',
            '--hidden-import=smtplib',
            'enhanced_main.py'  # Use our enhanced main file
        ]
        
        subprocess.check_call(cmd)
        print("✅ App built successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error building app: {e}")
        return False
    
    return True

def create_run_script():
    """Create a run script to set up the environment and run the app."""
    script_content = """#!/bin/bash

# JobHunter Run Script - Enhanced for Mac M2
# This script ensures the app has the necessary permissions and environment

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if .env file exists
if [ ! -f "$DIR/.env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create a .env file in $DIR with your email credentials:"
    echo ""
    echo "EMAIL_SENDER=your.email@gmail.com"
    echo "EMAIL_PASSWORD=your-app-password"
    echo "EMAIL_RECIPIENT=your.email@gmail.com"
    echo "SMTP_SERVER=smtp.gmail.com"
    echo "SMTP_PORT=587"
    echo ""
    echo "# Optional but recommended for better results:"
    echo "OPENAI_API_KEY=your-openai-api-key"
    echo ""
    read -p "Press any key to exit..."
    exit 1
fi

# Run the app (in onedir mode)
"$DIR/dist/JobHunter/JobHunter"

# Keep the window open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ An error occurred. Press any key to exit..."
    read -n 1
fi
"""
    
    with open('run_jobhunter.sh', 'w') as f:
        f.write(script_content)
    
    # Make the script executable
    os.chmod('run_jobhunter.sh', 0o755)
    
    print("✅ Created run_jobhunter.sh script")

def package_app():
    """Package the app with all necessary files."""
    print("📦 Packaging the app...")
    
    # Create a distribution directory
    dist_dir = 'JobHunter_App'
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # Copy the run script
    if os.path.exists('run_jobhunter.sh'):
        shutil.copy('run_jobhunter.sh', dist_dir)
    
    # For onedir mode, copy the entire dist/JobHunter directory
    if os.path.exists('dist/JobHunter'):
        shutil.copytree('dist/JobHunter', f'{dist_dir}/dist/JobHunter')
    
    # Create a sample .env file
    sample_env = """# Email configuration (required)
EMAIL_SENDER=your.email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENT=your.email@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# OpenAI API (optional but recommended for better results)
OPENAI_API_KEY=your-openai-api-key
"""
    
    with open(f'{dist_dir}/.env.example', 'w') as f:
        f.write(sample_env)
    
    # Create README for the distribution
    readme_content = """# JobHunter App for Mac M2 - With OpenAI Integration

This is the enhanced version of JobHunter with OpenAI integration for Mac M2 that works with all major job sites in Bangalore.

## Setup

1. Create a `.env` file in this directory by copying `.env.example`:
   ```
   cp .env.example .env
   ```

2. Edit the `.env` file with your credentials:
   - For Gmail, use an App Password (not your regular password)
   - Go to Google Account > Security > 2-Step Verification > App passwords
   - For OpenAI, get an API key from platform.openai.com (optional but recommended)

## Running the App

Run it in Terminal:
```
./run_jobhunter.sh
```

The app will:
- Search for jobs on Indeed, Naukri, Foundit, LinkedIn and company career pages
- Filter based on configured keywords and locations
- Send an email with the results

## Troubleshooting

- If you get permission errors, make sure the script is executable:
  ```
  chmod +x run_jobhunter.sh
  ```

- If Selenium-based scraping doesn't work, the app will automatically fall back to OpenAI (if configured)

- If neither works, you'll still get Indeed results which don't require Selenium

## Cost Considerations

This app uses GPT-3.5-turbo, the cheapest OpenAI model. Each run will typically cost less than $0.01 in API usage.
"""
    
    with open(f'{dist_dir}/README.md', 'w') as f:
        f.write(readme_content)
    
    print(f"✅ App packaged in {dist_dir}/")
    print("📝 To use the app:")
    print(f"   1. cd {dist_dir}")
    print("   2. Copy .env.example to .env and edit with your credentials")
    print("   3. Run ./run_jobhunter.sh")

def main():
    """Main function to build the app."""
    print("🚀 JobHunter App Builder for Mac M2 - With OpenAI Integration")
    print("=" * 50)
    
    # Check system
    if platform.system() != "Darwin":
        print("❌ This script is designed for macOS")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Build the app
    if not build_app():
        sys.exit(1)
    
    # Create run script
    create_run_script()
    
    # Package the app
    package_app()
    
    print("\n✅ Build completed successfully!")

if __name__ == "__main__":
    main()