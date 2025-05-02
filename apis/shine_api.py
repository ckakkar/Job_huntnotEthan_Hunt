"""Shine API for job search without Selenium."""
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import json
import re

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class ShineAPI:
    """
    Shine API for direct job data extraction.
    Uses structured data extraction from HTML.
    """
    
    def __init__(self):
        """Initialize the Shine API."""
        self.name = "Shine"
        self.base_url = "https://www.shine.com"
        self.search_url = "https://www.shine.com/job-search"
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
            "DNT": "1",
            "Cache-Control": "max-age=0"
        }
    
    def build_url(self, keywords, location, days=7):
        """
        Build the URL for Shine job search.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            days (int): Number of days to look back
            
        Returns:
            str: URL for Shine job search
        """
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        
        # Shine uses a different URL format
        return f"{self.search_url}/{encoded_keywords}-jobs-in-{encoded_location}"
    
    def extract_structured_data(self, html):
        """
        Extract job data from structured data in the HTML.
        
        Args:
            html (str): HTML content
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        
        # Look for JSON-LD structured data
        soup = BeautifulSoup(html, "html.parser")
        script_tags = soup.find_all("script", {"type": "application/ld+json"})
        
        for script in script_tags:
            try:
                data = json.loads(script.string)
                
                # Check if this is job posting data
                if isinstance(data, dict) and "@type" in data and data["@type"] == "JobPosting":
                    job = {
                        "title": data.get("title", ""),
                        "company": data.get("hiringOrganization", {}).get("name", ""),
                        "location": data.get("jobLocation", {}).get("address", {}).get("addressLocality", ""),
                        "date": data.get("datePosted", "Recent"),
                        "link": data.get("url", "")
                    }
                    jobs.append(job)
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "@type" in item and item["@type"] == "JobPosting":
                            job = {
                                "title": item.get("title", ""),
                                "company": item.get("hiringOrganization", {}).get("name", ""),
                                "location": item.get("jobLocation", {}).get("address", {}).get("addressLocality", ""),
                                "date": item.get("datePosted", "Recent"),
                                "link": item.get("url", "")
                            }
                            jobs.append(job)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return jobs
    
    def extract_jobs_from_html(self, html):
        """
        Extract job listings from HTML content.
        
        Args:
            html (str): HTML content from Shine search results
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")
        
        # First try structured data
        structured_jobs = self.extract_structured_data(html)
        if structured_jobs:
            return structured_jobs
        
        # Try to extract using Shine specific selectors
        job_cards = soup.select(".search_listing, .job_card_area, .jobCard, .w-100.mb-4, article[data-job-id]")
        
        for job in job_cards:
            try:
                # Extract title
                title_elem = job.select_one("h2 a, .job_title, .jobTitle, h3 a, .heading h2")
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Extract company
                company_elem = job.select_one(".company, .cName, .jobcompany, .top_company_text")
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Extract location
                location_elem = job.select_one(".location, .new_job_location, .jobLocation, .loc")
                location = location_elem.text.strip() if location_elem else "Bangalore"
                
                # Extract date
                date_elem = job.select_one(".posting_time, .post-date, span[data-date], .dates")
                date = date_elem.text.strip() if date_elem else "Recently Posted"
                
                # Extract link
                link = ""
                if title_elem.name == 'a' and title_elem.has_attr("href"):
                    href = title_elem["href"]
                    if href.startswith("http"):
                        link = href
                    else:
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
        Search for jobs on Shine.
        
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
        
        print(f"Searching Shine: {url}")
        
        try:
            # Process first page
            response = requests.get(url, headers=self.get_headers(), timeout=15)
            if response.status_code != 200:
                print(f"Failed to get response from Shine: {response.status_code}")
                return self.jobs_df
            
            jobs = self.extract_jobs_from_html(response.text)
            all_jobs.extend(jobs)
            
            # Process additional pages if needed
            if len(jobs) > 0 and len(all_jobs) < max_jobs and max_pages > 1:
                # Find pagination pattern
                for page in range(2, min(max_pages + 1, 6)):
                    page_url = f"{url}?page={page}"
                    
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
            print(f"Error searching Shine: {e}")
        
        # Convert to DataFrame
        for job in all_jobs[:max_jobs]:
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
        
        print(f"Found {len(self.jobs_df)} jobs from Shine")
        return self.jobs_df