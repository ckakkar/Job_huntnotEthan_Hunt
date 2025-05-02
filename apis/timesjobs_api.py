"""TimesJobs API for job search without Selenium."""
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import json
import re

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class TimesJobsAPI:
    """
    TimesJobs API for direct job data extraction.
    Uses structured data extraction from HTML.
    """
    
    def __init__(self):
        """Initialize the TimesJobs API."""
        self.name = "TimesJobs"
        self.base_url = "https://www.timesjobs.com"
        self.search_url = "https://www.timesjobs.com/candidate/job-search.html"
        self.jobs_df = pd.DataFrame(columns=["title", "company", "location", "date", "link", "source"])
    
    def get_headers(self):
        """Return the headers to use for requests."""
        return {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
    
    def build_url(self, keywords, location, days=7):
        """
        Build the URL for TimesJobs job search.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            days (int): Number of days to look back
            
        Returns:
            str: URL for TimesJobs job search
        """
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        
        # TimesJobs doesn't have a direct days filter, so we'll filter later
        return f"{self.search_url}?searchType=personalizedSearch&from=submit&txtKeywords={encoded_keywords}&txtLocation={encoded_location}"
    
    def extract_jobs_from_html(self, html):
        """
        Extract job listings from HTML content.
        
        Args:
            html (str): HTML content from TimesJobs search results
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")
        
        # TimesJobs job cards
        job_cards = soup.select(".job-bx-info, .job-listing, li[data-url]")
        
        for job in job_cards:
            try:
                # Extract title
                title_elem = job.select_one("h2 a, .clearfix h3 a, .job-listing a[title], h3.joblist-comp-name, [data-url] h2")
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Extract company
                company_elem = job.select_one(".joblist-comp-name, h3.joblist-comp-name, .company-name")
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Clean company (remove extra text like (More Jobs))
                company = re.sub(r'\(More.*\)', '', company).strip()
                
                # Extract location
                location_elem = job.select_one("ul li:nth-child(1), .locations, span.list-jobs")
                location = location_elem.text.strip() if location_elem else "Bangalore"
                
                # Extract date
                date_elem = job.select_one(".list-date, ul li:nth-child(3), [data-rel='date']")
                date = date_elem.text.strip() if date_elem else "Recently Posted"
                
                # Extract link
                link = ""
                if title_elem.name == 'a' and title_elem.has_attr("href"):
                    href = title_elem["href"]
                    if href.startswith("http"):
                        link = href
                    else:
                        link = urljoin(self.base_url, href)
                
                # If we don't have a link but the container has a data-url attribute
                if not link and job.has_attr("data-url"):
                    href = job["data-url"]
                    if href:
                        link = urljoin(self.base_url, href)
                
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "date": date,
                    "link": link
                })
            except Exception as e:
                print(f"Error extracting job details: {e}")
                continue
        
        return jobs
    
    def search(self, keywords, location, days=7, max_pages=3, max_jobs=MAX_JOBS_PER_SOURCE):
        """
        Search for jobs on TimesJobs.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            days (int): Number of days to look back
            max_pages (int): Maximum number of pages to scrape
            max_jobs (int): Maximum number of jobs to return
            
        Returns:
            pd.DataFrame: DataFrame containing job listings
        """
        all_jobs = []
        url = self.build_url(keywords, location, days)
        
        print(f"Searching TimesJobs: {url}")
        
        try:
            # Process first page
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            if response.status_code != 200:
                print(f"Failed to get response from TimesJobs: {response.status_code}")
                return self.jobs_df
            
            jobs = self.extract_jobs_from_html(response.text)
            all_jobs.extend(jobs)
            
            # Process additional pages if needed
            if len(jobs) > 0 and len(all_jobs) < max_jobs and max_pages > 1:
                # Find pagination pattern
                for page in range(2, min(max_pages + 1, 6)):
                    page_url = f"{url}&pageNum={page}"
                    
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(1, 2))
                    
                    try:
                        response = requests.get(page_url, headers=self.get_headers(), timeout=15)
                        if response.status_code == 200:
                            page_jobs = self.extract_jobs_from_html(response.text)
                            all_jobs.extend(page_jobs)
                            
                            if not page_jobs:
                                # No more jobs found, break early
                                break
                        else:
                            # Request failed, stop pagination
                            break
                    except Exception as e:
                        print(f"Error fetching page {page}: {e}")
                        break
                    
                    # Check if we've reached the maximum number of jobs
                    if len(all_jobs) >= max_jobs:
                        break
        
        except Exception as e:
            print(f"Error searching TimesJobs: {e}")
        
        # Convert to DataFrame - doing date filtering here
        filtered_jobs = []
        for job in all_jobs[:max_jobs]:
            # Filter by date if possible
            date_text = job["date"].lower()
            
            # Only include jobs posted within the requested timeframe
            include_job = True
            if days <= 7:
                # Look for date indicators
                if "month" in date_text or "months" in date_text:
                    include_job = False
                if "week" in date_text and not "a week" in date_text and not "1 week" in date_text:
                    match = re.search(r'(\d+)\s*week', date_text)
                    if match and int(match.group(1)) > days/7:
                        include_job = False
            
            if include_job:
                filtered_jobs.append(job)
        
        # Convert filtered jobs to DataFrame
        for job in filtered_jobs:
            self.jobs_df = pd.concat([
                self.jobs_df,
                pd.DataFrame({
                    "title": [job["title"]],
                    "company": [job["company"]],
                    "location": [job["location"]],
                    "date": [job["date"]],
                    "link": [job["link"]],
                    "source": [self.name]
                })
            ], ignore_index=True)
        
        print(f"Found {len(self.jobs_df)} jobs from TimesJobs")
        return self.jobs_df