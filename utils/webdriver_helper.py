"""Reliable webdriver setup for Mac M2 and other platforms."""
import os
import platform
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.safari.options import Options as SafariOptions
from webdriver_manager.chrome import ChromeDriverManager

def ensure_chromedriver():
    """
    Ensures ChromeDriver is installed and properly configured, especially for Mac M2.
    
    Returns:
        bool: True if successful, False otherwise
    """
    is_m2_mac = platform.system() == "Darwin" and platform.machine() == "arm64"
    
    if is_m2_mac:
        print("🍎 Detected Mac M2, using optimized ChromeDriver setup...")
        
        # Check if chromedriver is installed via Homebrew
        try:
            result = subprocess.run(["which", "chromedriver"], capture_output=True, text=True)
            chromedriver_path = result.stdout.strip()
            
            if chromedriver_path:
                print(f"✅ Found ChromeDriver at: {chromedriver_path}")
                
                # Try to remove quarantine attribute
                try:
                    subprocess.run(["xattr", "-d", "com.apple.quarantine", chromedriver_path], 
                                  check=False, capture_output=True)
                    print("✅ Removed quarantine attribute from ChromeDriver")
                except Exception:
                    print("⚠️ Could not remove quarantine attribute, but ChromeDriver might still work")
                
                return True
            else:
                print("⚠️ ChromeDriver not found in PATH")
                
                # Check if Chrome is installed
                chrome_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chrome.app/Contents/MacOS/Chrome"
                ]
                
                chrome_exists = any(os.path.exists(path) for path in chrome_paths)
                
                if chrome_exists:
                    print("✅ Google Chrome is installed")
                    print("⚠️ Please install ChromeDriver manually with: brew install --cask chromedriver")
                    print("⚠️ Then run: xattr -d com.apple.quarantine /usr/local/bin/chromedriver")
                else:
                    print("⚠️ Google Chrome is not installed")
                    print("⚠️ Please install Google Chrome first, then ChromeDriver")
                
                return False
            
        except Exception as e:
            print(f"⚠️ Error checking ChromeDriver: {e}")
            return False
    
    # For non-M2 systems, assume ChromeDriver can be managed automatically
    return True

def setup_webdriver(headless=True, use_safari_fallback=True):
    """
    Set up a WebDriver optimized for the current platform.
    
    Args:
        headless (bool): Whether to run the browser in headless mode
        use_safari_fallback (bool): Whether to try Safari if Chrome fails
    
    Returns:
        webdriver: A configured WebDriver instance or None if setup fails
    """
    is_m2_mac = platform.system() == "Darwin" and platform.machine() == "arm64"
    
    # Try Chrome first
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        
        # Add language for international sites
        chrome_options.add_argument("--lang=en-US,en;q=0.9")
        
        # Set user agent to avoid blocking
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        
        # Try direct path for M2 Macs first
        if is_m2_mac:
            driver_paths = [
                "/usr/local/bin/chromedriver",
                "/opt/homebrew/bin/chromedriver"
            ]
            
            for path in driver_paths:
                if os.path.exists(path):
                    print(f"Using ChromeDriver from: {path}")
                    service = Service(executable_path=path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    return driver
            
            # If direct path failed, try binary location
            chrome_binaries = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome"
            ]
            
            for binary in chrome_binaries:
                if os.path.exists(binary):
                    chrome_options.binary_location = binary
                    print(f"Setting Chrome binary location: {binary}")
        
        # Fall back to ChromeDriverManager
        print("Using ChromeDriverManager...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
        
    except Exception as e:
        print(f"Chrome WebDriver setup failed: {e}")
        
        # Try Safari on Mac as last resort
        if use_safari_fallback and platform.system() == "Darwin":
            try:
                print("Trying Safari as fallback...")
                safari_options = SafariOptions()
                driver = webdriver.Safari(options=safari_options)
                return driver
            except Exception as safari_error:
                print(f"Safari WebDriver setup also failed: {safari_error}")
        
        return None

def scroll_to_load_dynamic_content(driver, scroll_pause_time=1.0, num_scrolls=5):
    """
    Scroll down the page to load dynamic content.
    
    Args:
        driver: Selenium WebDriver instance
        scroll_pause_time (float): Time to pause between scrolls
        num_scrolls (int): Number of times to scroll
    """
    for i in range(num_scrolls):
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait to load page
        time.sleep(scroll_pause_time)
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # Break if reached the bottom
        if i > 0 and new_height == last_height:
            break
            
        last_height = new_height