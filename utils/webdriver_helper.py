"""Reliable webdriver setup for Mac M2 and other platforms."""
import os
import platform
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.safari.options import Options as SafariOptions

def ensure_chromedriver():
    """
    Ensures ChromeDriver is installed and properly configured.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Just check if ChromeDriver is in PATH
    try:
        result = subprocess.run(["which", "chromedriver"], capture_output=True, text=True)
        chromedriver_path = result.stdout.strip()
        
        if chromedriver_path:
            print(f"✅ Found ChromeDriver at: {chromedriver_path}")
            return True
        else:
            print("⚠️ ChromeDriver not found in PATH")
            return False
    except Exception as e:
        print(f"⚠️ Error checking ChromeDriver: {e}")
        return False

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
    
    # Find ChromeDriver path - use the one installed by Homebrew
    result = subprocess.run(["which", "chromedriver"], capture_output=True, text=True)
    chromedriver_path = result.stdout.strip()
    
    if not chromedriver_path:
        print("❌ ChromeDriver not found in PATH. Try Safari instead.")
        if use_safari_fallback and platform.system() == "Darwin":
            try:
                print("🍎 Trying Safari as fallback...")
                safari_options = SafariOptions()
                driver = webdriver.Safari(options=safari_options)
                print("✅ Safari WebDriver created successfully!")
                return driver
            except Exception as safari_error:
                print(f"❌ Safari WebDriver setup failed: {safari_error}")
                return None
        return None
    
    print(f"Using ChromeDriver from: {chromedriver_path}")
    
    # Try Chrome
    try:
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        
        # User agent to avoid blocking
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        
        # Set Chrome binary location for M2 Macs
        if is_m2_mac:
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chrome.app/Contents/MacOS/Chrome"
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    chrome_options.binary_location = chrome_path
                    print(f"Set Chrome binary location: {chrome_path}")
                    break
        
        # Create Chrome WebDriver with direct path
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✅ Chrome WebDriver created successfully!")
        return driver
    except Exception as e:
        print(f"❌ Chrome WebDriver setup failed: {e}")
        
        # Try Safari on Mac as fallback
        if use_safari_fallback and platform.system() == "Darwin":
            try:
                print("🍎 Trying Safari as fallback...")
                safari_options = SafariOptions()
                driver = webdriver.Safari(options=safari_options)
                print("✅ Safari WebDriver created successfully!")
                return driver
            except Exception as safari_error:
                print(f"❌ Safari WebDriver setup failed: {safari_error}")
                return None
        
        return None

def scroll_to_load_dynamic_content(driver, scroll_pause_time=1.0, num_scrolls=5):
    """
    Scroll down the page to load dynamic content.
    
    Args:
        driver: Selenium WebDriver instance
        scroll_pause_time (float): Time to pause between scrolls
        num_scrolls (int): Number of times to scroll
    """
    last_height = 0
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