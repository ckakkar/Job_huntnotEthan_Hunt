#!/usr/bin/env python3
"""
Enhanced Job Hunter - API and AI-powered comprehensive job search
Multiple fallback mechanisms and improved job discovery
"""
import pandas as pd
import time
import sys
import os
import random
from dotenv import load_dotenv
import traceback
from datetime import datetime
import concurrent.futures

# Load environment variables
load_dotenv()

# Import APIs
from apis.indeed_api import IndeedAPI
from apis.linkedin_api import LinkedInAPI
from apis.naukri_api import NaukriAPI
from apis.foundit_api import FounditAPI
from apis.timesjobs_api import TimesJobsAPI
from apis.shine_api import ShineAPI

# Import our OpenAI scraper
from openai_scraper import OpenAIScraper

# Import direct HTML scraper as fallback
from direct_scraper import DirectScraper

# Import email alert
from alert.email_alert import EmailAlert

# Import utilities
from utils.data_processor import process_jobs, filter_jobs_by_title_keywords

# Import configuration
from config.config import JOB_KEYWORDS, LOCATIONS, JOB_PORTALS, COMPANY_CAREER_PAGES


def display_progress(message):
    """Display progress message with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def search_with_api(api_class, keywords_str, location_str, recent_days, semaphore=None):
    """
    Search for jobs using an API with proper error handling.
    
    Args:
        api_class: The API class to instantiate and use
        keywords_str (str): Keywords to search for
        location_str (str): Location to search in
        recent_days (int): Number of days to look back
        semaphore: Optional semaphore for throttling concurrent requests
        
    Returns:
        pd.DataFrame: DataFrame with job listings
    """
    try:
        if semaphore:
            with semaphore:
                api = api_class()
                display_progress(f"🔍 Searching {api.name}...")
                # Handle different parameter names between APIs
                if api_class.__name__ == "LinkedInAPI":
                    # LinkedIn uses time_period instead of days
                    time_period = "past-week" if recent_days >= 7 else "24h"
                    return api.search(keywords_str, location_str, time_period=time_period)
                else:
                    return api.search(keywords_str, location_str, days=recent_days)
        else:
            api = api_class()
            display_progress(f"🔍 Searching {api.name}...")
            # Handle different parameter names between APIs
            if api_class.__name__ == "LinkedInAPI":
                # LinkedIn uses time_period instead of days
                time_period = "past-week" if recent_days >= 7 else "24h"
                return api.search(keywords_str, location_str, time_period=time_period)
            else:
                return api.search(keywords_str, location_str, days=recent_days)
    except Exception as e:
        display_progress(f"❌ Error with {api_class.__name__}: {e}")
        traceback.print_exc(limit=2)
        return pd.DataFrame(columns=["title", "company", "location", "date", "link", "source"])


def run_job_search(keywords_list=None, location_str=None, recent_days=7, use_concurrent=True):
    """
    Run the job search process with API and AI methods with multiple fallbacks.
    
    Args:
        keywords_list (list): List of keywords to search for
        location_str (str): Location to search in
        recent_days (int): Number of days to look back for recent jobs
        use_concurrent (bool): Whether to use concurrent processing
    
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
    
    # APPROACH 1: Use Direct APIs in parallel
    display_progress("🌟 Using direct APIs for major job sites...")
    
    api_classes = [
        IndeedAPI,
        LinkedInAPI,
        NaukriAPI,
        FounditAPI,
        TimesJobsAPI,
        ShineAPI
    ]
    
    if use_concurrent:
        # Use concurrent.futures to run API calls in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Map each API class to a future
            future_to_api = {
                executor.submit(search_with_api, api_class, keywords_str, location_str, recent_days): 
                api_class.__name__ for api_class in api_classes
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_api):
                api_name = future_to_api[future]
                try:
                    jobs_df = future.result()
                    if not jobs_df.empty:
                        display_progress(f"✅ Found {len(jobs_df)} jobs from {api_name}")
                        all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                except Exception as e:
                    display_progress(f"❌ Error with {api_name}: {e}")
    else:
        # Sequential processing
        for api_class in api_classes:
            jobs_df = search_with_api(api_class, keywords_str, location_str, recent_days)
            if not jobs_df.empty:
                all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
    
    # APPROACH 2: Use OpenAI for sites that direct APIs can't handle
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key:
        display_progress("🧠 Using OpenAI to scrape additional sites...")
        
        # Get already scraped sources to avoid duplicates
        scraped_sources = all_jobs["source"].unique().tolist() if not all_jobs.empty else []
        
        # Finance-focused job boards and company sites
        openai_sites = [
            # Finance-specific job boards
            {"name": "eFinancialCareers", "url": "https://www.efinancialcareers.com/jobs-Finance-Accounting-Bangalore.s016"},
            {"name": "FinancialJobBank", "url": "https://www.financialjobbank.com/search-jobs?keywords={keywords}&location=Bangalore"},
            
            # Company career pages
            {"name": "JPMorgan", "url": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?location=Bengaluru"},
            {"name": "Goldman Sachs", "url": "https://www.goldmansachs.com/careers/professionals/positions-for-experienced-professionals.html?city=Bengaluru"},
            {"name": "State Street", "url": "https://statestreet.wd1.myworkdayjobs.com/en-US/Global/jobs?locations=be03a623dbe601d38a65c3391d4d1970"},
            {"name": "Morgan Stanley", "url": "https://www.morganstanley.com/careers/career-search.html?city=Bangalore"},
            {"name": "Citibank", "url": "https://jobs.citi.com/search-jobs/Bangalore"},
            {"name": "HSBC", "url": "https://www.hsbc.com/careers/find-a-job?locationContains=Bangalore"},
            {"name": "Deloitte", "url": "https://apply.deloitte.com/careers/SearchJobs/Bangalore"},
            {"name": "EY", "url": "https://careers.ey.com/ey/search/?location=Bangalore"},
            {"name": "Northern Trust", "url": "https://careers.northerntrust.com/jobs/search/17313739"},
            {"name": "Deutsche Bank", "url": "https://careers.db.com/professional-careers/search-roles"},
            {"name": "BNY Mellon", "url": "https://www.bnymellon.com/us/en/careers/job-search.html"}
        ]
        
        # Process sites with OpenAI, with fallback to direct scraping
        for site in openai_sites:
            # Skip if already have results from this source
            if site["name"] in scraped_sources:
                continue
                
            try:
                display_progress(f"🧠 Using OpenAI to scrape {site['name']}...")
                scraper = OpenAIScraper(site["name"], site["url"], openai_api_key)
                jobs_df = scraper.scrape(keywords_str, location_str)
                
                # If OpenAI returned results, add them
                if not jobs_df.empty:
                    all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                    display_progress(f"✅ Found {len(jobs_df)} jobs from {site['name']} via OpenAI")
                    scraped_sources.append(site["name"])
                else:
                    # Fallback to direct HTML scraping if OpenAI returned no results
                    display_progress(f"⚠️ No results from OpenAI for {site['name']}. Trying direct scraping...")
                    direct_scraper = DirectScraper(site["name"], site["url"])
                    direct_jobs_df = direct_scraper.scrape(keywords_str, location_str)
                    
                    if not direct_jobs_df.empty:
                        all_jobs = pd.concat([all_jobs, direct_jobs_df], ignore_index=True)
                        display_progress(f"✅ Found {len(direct_jobs_df)} jobs from {site['name']} via direct scraping")
                        scraped_sources.append(site["name"])
                
                # Random delay between requests
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                display_progress(f"❌ Error scraping {site['name']}: {e}")
    else:
        display_progress("⚠️ OpenAI API key not found. Skipping AI-assisted scraping.")
    
    # If we still have no jobs, try a more aggressive direct scraping approach
    if all_jobs.empty or len(all_jobs) < 10:
        display_progress("⚠️ Few or no jobs found. Trying aggressive scraping approach...")
        
        aggressive_sites = [
            {"name": "LinkedIn", "url": "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}"},
            {"name": "Indeed", "url": "https://in.indeed.com/jobs?q={keywords}&l={location}"},
            {"name": "Naukri", "url": "https://www.naukri.com/jobs-in-{location}?keywordsearch={keywords}"},
            {"name": "Foundit", "url": "https://www.foundit.in/srp/results?keyword={keywords}&location={location}"}
        ]
        
        for site in aggressive_sites:
            if site["name"] not in scraped_sources:
                try:
                    display_progress(f"🔍 Aggressive scraping of {site['name']}...")
                    direct_scraper = DirectScraper(site["name"], site["url"])
                    jobs_df = direct_scraper.scrape(keywords_str, location_str, aggressive=True)
                    
                    if not jobs_df.empty:
                        all_jobs = pd.concat([all_jobs, jobs_df], ignore_index=True)
                        display_progress(f"✅ Found {len(jobs_df)} jobs from {site['name']} via aggressive scraping")
                except Exception as e:
                    display_progress(f"❌ Error in aggressive scraping of {site['name']}: {e}")
    
    # Process jobs with less aggressive filtering
    display_progress("🔄 Processing jobs...")
    processed_jobs = process_jobs(
        all_jobs,
        keywords=keywords_list,
        locations=LOCATIONS,
        recent_days=30,  # More generous timeframe
        sort_by_date=True
    )
    
    # If too few jobs, skip the finance-specific filtering
    if len(processed_jobs) > 25:
        display_progress("🏦 Applying additional filtering for finance/banking roles...")
        finance_keywords = ["finance", "banking", "investment", "regulatory", "compliance", "treasury", 
                           "risk", "analyst", "financial", "portfolio", "operations"]
        
        # Only apply if we have enough jobs
        finance_filtered = filter_jobs_by_title_keywords(processed_jobs, finance_keywords)
        if not finance_filtered.empty and len(finance_filtered) >= 10:
            processed_jobs = finance_filtered
    
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
        print("🚀 Enhanced Job Hunter - Multi-Method Job Search - Last 7 Days")
        print("="*70 + "\n")
        
        # Check if .env file exists
        if not os.path.exists('.env'):
            display_progress("❌ .env file not found. Please create one with your credentials")
            sys.exit(1)
        
        # Search for jobs - use concurrent processing by default
        jobs_df = run_job_search(recent_days=7, use_concurrent=True)
        
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