"""Base scraper optimized for Mac M2."""
import time
import requests
import platform
import os
import pandas as pd
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from config.config import USER_AGENT, REQUEST_DELAY


class BaseScraper(ABC):
    """Base class for all job scrapers with Mac M2 optimizations."""
    
    def __init__(self, name):
        """Initialize the scraper with a name."""
        self.name = name
        self.jobs_df = pd.DataFrame(columns=["title", "company", "location", "date", "link", "source"])
        
    def get_user_agent(self):
        """Return the user agent to use for requests."""
        return USER_AGENT
    
    def get_headers(self):
        """Return the headers to use for requests."""
        return {
            "User-Agent": self.get_user_agent()
        }
    
    def make_request(self, url):
        """Make a request to the given URL and return the response."""
        try:
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            time.sleep(REQUEST_DELAY)  # Be polite with delays
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return None
    
    def setup_selenium(self, headless=True):
        """Set up Selenium webdriver optimized for Mac M2."""
        is_m2_mac = platform.system() == "Darwin" and platform.machine() == "arm64"
        
        try:
            if is_m2_mac:
                # Mac M2 specific configuration
                print(f"🍎 Setting up Chrome for Mac M2 (arm64)...")
                
                # Specific options for M2 Mac
                options = webdriver.ChromeOptions()
                if headless:
                    options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument(f"user-agent={self.get_user_agent()}")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")
                
                # Set binary location for Chrome on Mac
                if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                
                # Try to use ChromeDriverManager to manage driver versions
                try:
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    return driver
                except Exception as e:
                    print(f"ChromeDriverManager failed: {e}, trying manual configuration...")
                    
                    # If that fails, try a more direct approach
                    if os.path.exists("/usr/local/bin/chromedriver"):
                        service = Service("/usr/local/bin/chromedriver")
                        driver = webdriver.Chrome(service=service, options=options)
                        return driver
                    
                    print("Failed to find a compatible chromedriver. Please install it manually.")
                    return None
            else:
                # Standard configuration for other platforms
                options = webdriver.ChromeOptions()
                if headless:
                    options.add_argument("--headless=new")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument(f"user-agent={self.get_user_agent()}")
                
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                return driver
                
        except Exception as e:
            print(f"Error setting up Selenium: {e}")
            return None
    
    def add_job(self, title, company, location, date, link):
        """Add a job to the dataframe."""
        new_job = pd.DataFrame({
            "title": [title],
            "company": [company],
            "location": [location],
            "date": [date],
            "link": [link],
            "source": [self.name]
        })
        self.jobs_df = pd.concat([self.jobs_df, new_job], ignore_index=True)
    
    def get_jobs(self):
        """Return the dataframe of jobs."""
        return self.jobs_df
    
    @abstractmethod
    def scrape(self, keywords, location, max_jobs=25):
        """
        Scrape jobs for the given keywords and location.
        
        Args:
            keywords (str): Keywords to search for.
            location (str): Location to search in.
            max_jobs (int): Maximum number of jobs to scrape.
            
        Returns:
            pd.DataFrame: Dataframe with the scraped jobs.
        """
        pass