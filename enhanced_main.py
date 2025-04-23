#!/usr/bin/env python3
"""
Enhanced Job Hunter - Comprehensive job search across multiple platforms
Optimized for Mac M2 with multiple fallback methods
"""
import pandas as pd
import time
import sys
import os
import random
from dotenv import load_dotenv
import traceback
from datetime import datetime

# Load environment variables
load_dotenv()

# Import APIs and scrapers
try:
    from apis.indeed_api import IndeedAPI
    from apis.linkedin_api import LinkedInAPI
    from apis.github_jobs_api import GitHubJobsAPI
    APIS_AVAILABLE = True
except ImportError:
    APIS_AVAILABLE = False
    print("APIs not available. Using scrapers only.")

# Import our OpenAI scraper
from openai_scraper import OpenAIScraper

# Import email alert
from alert.email_alert import EmailAlert

# Import utilities
from utils.data_processor import process_jobs
from utils.webdriver_helper import setup_webdriver, ensure_chromedriver

# Import configuration
from config.config import JOB_KEYWORDS, LOCATIONS, JOB_PORTALS, COMPANY_CAREER_PAGES

# Try to import Selenium-based scrapers but have fallbacks
try:
    from scrapers.indeed import IndeedScraper
    from scrapers.naukri import NaukriScraper
    from scrapers.foundit import FounditScraper
    from scrapers.company_careers import get_company_scrapers, CompanyCareerScraper
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium not available. Using APIs and OpenAI instead.")


def display_progress(message):
    """Display progress message with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def get_driver():
    """Get a webdriver with proper error handling."""
    try:
        # First make sure ChromeDriver is properly set up
        ensure_chromedriver()
        
        # Then set up the WebDriver
        driver = setup_webdriver(headless=True)
        if driver:
            return driver
        else:
            display_progress("⚠️ Failed to set up WebDriver. Using APIs and OpenAI instead.")
            return None
    except Exception as e:
        display_progress(f"⚠️ Error setting up WebDriver: {e}")
        return None


def run_job_search(keywords_list=None, location_str=None, recent_days=7):
    """
    Run the job search process with multiple methods and fallbacks.
    
    Args:
        keywords_list (list): List of keywords to search for
        location_str (str): Location to search in
        recent_days (int): Number of days to look back for recent jobs
    
    Returns:
        pd.DataFrame: DataFrame with job listings
    """
    # Use command line arguments if provided, otherwise use config
    keywords_list = keywords_list if keywords_list else JOB_KEYWORDS
    location_str = location_str if location_str else LOCATIONS[0]
    
    # Convert keywords list to a space-separated string for searching
    keywords_str = " OR ".join(keywords_list)
    
    display_progress(f"🔍 Searching for jobs with keywords: {keywords_str}")
    display_progress(f"📍 Location: {location_str}")
    display_progress(f"⏰ Timeframe: Last {recent_days} days")
    
    # Initialize dataframe to store all jobs
    all_jobs = pd.DataFrame(columns=["title", "company", "location", "date", "link", "source"])
    
    # APPROACH 1: Use Direct APIs (Most Reliable)
    if APIS_AVAILABLE:
        display_progress("🌟 Using direct APIs for major job sites...")
        
        # Indeed API
        try:
            display_progress("🔍 Searching Indeed API...")
            indeed_api = IndeedAPI()
            jobs_df = indeed_api.search(keywords_str, location_str, days=recent_days)
            if not jobs_df.empty:
                all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                display_progress(f"✅ Found {len(jobs_df)} jobs from Indeed API")
        except Exception as e:
            display_progress(f"❌ Error with Indeed API: {e}")
        
        # LinkedIn API
        try:
            display_progress("🔍 Searching LinkedIn API...")
            linkedin_api = LinkedInAPI()
            # Use past-week time period for 7 days
            time_period = "past-week" if recent_days >= 7 else "24h" if recent_days <= 1 else "past-week"
            jobs_df = linkedin_api.search(keywords_str, location_str, time_period=time_period)
            if not jobs_df.empty:
                all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                display_progress(f"✅ Found {len(jobs_df)} jobs from LinkedIn API")
        except Exception as e:
            display_progress(f"❌ Error with LinkedIn API: {e}")
        
        # GitHub Jobs API (for tech positions)
        try:
            github_api = GitHubJobsAPI()
            if github_api.is_available():
                display_progress("🔍 Searching GitHub Jobs API...")
                jobs_df = github_api.search(keywords_str, location_str, days=recent_days)
                if not jobs_df.empty:
                    all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                    display_progress(f"✅ Found {len(jobs_df)} jobs from GitHub Jobs")
        except Exception as e:
            display_progress(f"❌ Error with GitHub Jobs API: {e}")
    
    # APPROACH 2: Use Selenium-based scrapers if available
    if SELENIUM_AVAILABLE:
        display_progress("🌐 Using Selenium for job portals...")
        
        # Get a WebDriver for Selenium
        driver = get_driver()
        
        if driver:
            # Indeed
            try:
                display_progress("🔍 Scraping Indeed with Selenium...")
                scraper = IndeedScraper()
                jobs_df = scraper.scrape(keywords_str, location_str, days=recent_days)
                if not jobs_df.empty:
                    all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                    display_progress(f"✅ Found {len(jobs_df)} jobs from Indeed scraper")
            except Exception as e:
                display_progress(f"❌ Error scraping Indeed: {e}")
                traceback.print_exc()
            
            # Naukri
            try:
                display_progress("🔍 Scraping Naukri...")
                scraper = NaukriScraper()
                jobs_df = scraper.scrape(keywords_str, location_str, days=recent_days)
                if not jobs_df.empty:
                    all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                    display_progress(f"✅ Found {len(jobs_df)} jobs from Naukri")
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                display_progress(f"❌ Error scraping Naukri: {e}")
                traceback.print_exc()
            
            # Foundit
            try:
                display_progress("🔍 Scraping Foundit...")
                scraper = FounditScraper()
                jobs_df = scraper.scrape(keywords_str, location_str, days=recent_days)
                if not jobs_df.empty:
                    all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                    display_progress(f"✅ Found {len(jobs_df)} jobs from Foundit")
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                display_progress(f"❌ Error scraping Foundit: {e}")
                traceback.print_exc()
            
            # Company career pages
            display_progress("🏢 Scraping company career pages...")
            for company_config in COMPANY_CAREER_PAGES:
                try:
                    display_progress(f"🔍 Scraping {company_config['name']} career page...")
                    scraper = CompanyCareerScraper(company_config)
                    jobs_df = scraper.scrape(keywords_str, location_str)
                    if not jobs_df.empty:
                        all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                        display_progress(f"✅ Found {len(jobs_df)} jobs from {company_config['name']}")
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    display_progress(f"❌ Error scraping {company_config['name']}: {e}")
                    traceback.print_exc()
            
            # Close the driver
            try:
                driver.quit()
            except:
                pass
        else:
            display_progress("⚠️ Selenium WebDriver not available. Falling back to other methods.")
    
    # APPROACH 3: Use OpenAI for sites that are hard to scrape
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        display_progress("🧠 Using OpenAI to scrape additional sites...")
        
        # Get already scraped sources
        scraped_sources = all_jobs["source"].unique().tolist() if not all_jobs.empty else []
        
        # Sites to scrape with OpenAI - prioritize those not already scraped
        openai_sites = [
            # Standard job boards not already scraped
            {"name": "Naukri", "url": f"https://www.naukri.com/jobs-in-{{location}}?keywordsearch={{keywords}}&experience=0&jobAge={recent_days}"},
            {"name": "Foundit", "url": f"https://www.foundit.in/srp/results?keyword={{keywords}}&location={{location}}&sort=0&postDate={recent_days}"},
            {"name": "LinkedIn", "url": "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_TPR=r604800"},
            {"name": "TimesJobs", "url": "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={keywords}&txtLocation={location}"},
            
            # Company career pages not already scraped
            {"name": "JPMorgan", "url": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?location=Bengaluru"},
            {"name": "Goldman Sachs", "url": "https://www.goldmansachs.com/careers/professionals/positions-for-experienced-professionals.html?city=Bengaluru"},
            {"name": "State Street", "url": "https://statestreet.wd1.myworkdayjobs.com/en-US/Global/jobs?locations=be03a623dbe601d38a65c3391d4d1970"},
            # Additional sites for Bangalore
            {"name": "Shine", "url": "https://www.shine.com/job-search/jobs-in-bangalore"},
            {"name": "SimplyHired", "url": "https://www.simplyhired.co.in/search?q={keywords}&l=Bangalore"}
        ]
        
        for site in openai_sites:
            # Only use OpenAI for sites that weren't already successfully scraped
            if site["name"] not in scraped_sources:
                try:
                    display_progress(f"🧠 Using OpenAI to scrape {site['name']}...")
                    scraper = OpenAIScraper(site["name"], site["url"], openai_api_key)
                    jobs_df = scraper.scrape(keywords_str, location_str)
                    
                    # If we got results, add them
                    if not jobs_df.empty:
                        all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                        display_progress(f"✅ Found {len(jobs_df)} jobs from {site['name']} via OpenAI")
                        time.sleep(random.uniform(2, 4))
                except Exception as e:
                    display_progress(f"❌ Error with OpenAI scraper for {site['name']}: {e}")
    else:
        display_progress("⚠️ OpenAI API key not found. Skipping AI-assisted scraping.")
    
    # Process jobs
    display_progress("🔄 Processing jobs...")
    processed_jobs = process_jobs(
        all_jobs,
        keywords=keywords_list,
        locations=LOCATIONS,
        recent_days=recent_days,
        sort_by_date=True
    )
    
    display_progress(f"✅ Found {len(processed_jobs)} jobs matching your criteria")
    
    return processed_jobs


def send_alerts(jobs_df):
    """
    Send email alerts for the job listings.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame with job listings.
    """
    if jobs_df.empty:
        display_progress("ℹ️ No jobs to send alerts for")
        return
    
    # Send email alert
    display_progress("📧 Sending email alert...")
    email_alert = EmailAlert()
    if email_alert.is_enabled():
        success = email_alert.send_alert(jobs_df)
        if success:
            display_progress("✅ Email alert sent successfully")
        else:
            display_progress("❌ Failed to send email alert")
    else:
        display_progress("❌ Email alerts not configured. Please check your .env file")


def main():
    """Main function to run the job search."""
    try:
        # Display startup banner
        print("\n" + "="*70)
        print("🚀 Enhanced Job Hunter - Jobs Posted in the Last 7 Days")
        print("="*70 + "\n")
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            display_progress("❌ .env file not found. Please create one with your credentials")
            sys.exit(1)
        
        # Search for jobs
        jobs_df = run_job_search(recent_days=7)  # Get jobs from last 7 days
        
        # Send alerts if jobs were found
        if not jobs_df.empty:
            send_alerts(jobs_df)
        
        # Display summary
        print("\n" + "="*70)
        display_progress("🏁 Job search completed")
        display_progress(f"📊 Total jobs found: {len(jobs_df)}")
        
        # Show breakdown by source
        if not jobs_df.empty:
            source_counts = jobs_df['source'].value_counts()
            display_progress("📊 Jobs by source:")
            for source, count in source_counts.items():
                display_progress(f"  - {source}: {count} jobs")
        
        # Show today's date and time
        now = datetime.now()
        display_progress(f"📅 Search completed on {now.strftime('%Y-%m-%d at %H:%M:%S')}")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n")
        display_progress("🛑 Job search interrupted by user")
        sys.exit(0)
    except Exception as e:
        display_progress(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()