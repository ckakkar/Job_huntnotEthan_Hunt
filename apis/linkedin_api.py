"""LinkedIn API and structured scraper for reliable job data."""
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import json
import re

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class LinkedInAPI:
    """
    LinkedIn API and enhanced structured scraper.
    This combines direct scraping with structured data extraction.
    """
    
    def __init__(self):
        """Initialize the LinkedIn API."""
        self.name = "LinkedIn"
        self.base_url = "https://www.linkedin.com"
        self.search_url = "https://www.linkedin.com/jobs/search"
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
            "Sec-Fetch-User": "?1"
        }
    
    def build_url(self, keywords, location, time_period="past-week"):
        """
        Build the URL for LinkedIn job search.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            time_period (str): Time period to search for (24h, past-week, etc.)
            
        Returns:
            str: URL for LinkedIn job search
        """
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        
        # r604800 = past week (7 days)
        time_filter = "r24" if time_period == "24h" else "r604800" if time_period == "past-week" else ""
        time_param = f"&f_TPR={time_filter}" if time_filter else ""
        
        return f"{self.search_url}/?keywords={encoded_keywords}&location={encoded_location}{time_param}&sortBy=DD"
    
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
                
                # Handle array of job postings
                if isinstance(data, list):
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
                
                # Handle single job posting
                elif isinstance(data, dict) and "@type" in data:
                    if data["@type"] == "JobPosting":
                        job = {
                            "title": data.get("title", ""),
                            "company": data.get("hiringOrganization", {}).get("name", ""),
                            "location": data.get("jobLocation", {}).get("address", {}).get("addressLocality", ""),
                            "date": data.get("datePosted", "Recent"),
                            "link": data.get("url", "")
                        }
                        jobs.append(job)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return jobs
    
    def scrape_jobs_from_html(self, html):
        """
        Extract job details from LinkedIn HTML.
        
        Args:
            html (str): HTML content from LinkedIn search results
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")
        
        # First try to extract structured data
        structured_jobs = self.extract_structured_data(html)
        if structured_jobs:
            return structured_jobs
        
        # Try different selectors for job cards
        job_cards = soup.select(".jobs-search-results__list-item, .job-search-card, .base-card.job-card")
        
        for job in job_cards:
            try:
                # Title and link
                title_elem = job.select_one(".base-search-card__title, .job-search-card__title, .base-card__full-link, .job-card-container__link")
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Link could be in the title element or a parent
                link_elem = title_elem if title_elem.name == "a" else job.select_one("a.base-card__full-link, a.job-search-card__link")
                link = ""
                if link_elem and link_elem.has_attr("href"):
                    href = link_elem["href"]
                    if href.startswith("/"):
                        link = urljoin(self.base_url, href)
                    else:
                        link = href
                
                # Company
                company_elem = job.select_one(".base-search-card__subtitle, .job-search-card__subtitle a, .base-card__metadata a:first-child")
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Location
                location_elem = job.select_one(".job-search-card__location, span.job-search-card__location, .base-card__metadata span.job-search-card__location")
                location = location_elem.text.strip() if location_elem else "Remote/Unspecified"
                
                # Date - look for a time element
                date_elem = job.select_one("time, .job-search-card__listdate, .base-card__metadata time")
                date = date_elem.text.strip() if date_elem else "Within 7 days"
                
                # If there is no visible date, try to get it from attributes
                if not date or date == "Within 7 days":
                    if date_elem and date_elem.has_attr("datetime"):
                        date = "Within 7 days"  # Fallback if we can't parse the date
                
                # Ensure we have a link - if not, try to build one
                if not link and "linkedin.com" in self.base_url:
                    job_id = job.get("data-id", "")
                    if job_id:
                        link = f"https://www.linkedin.com/jobs/view/{job_id}/"
                    else:
                        # Try to extract ID from job card
                        job_id_match = re.search(r'data-job-id=["\']([^"\']+)["\']', str(job))
                        if job_id_match:
                            job_id = job_id_match.group(1)
                            link = f"https://www.linkedin.com/jobs/view/{job_id}/"
                
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
        
        # Additional method: look for job cards in a different format
        if not jobs:
            job_cards = soup.select("[data-job-id]")
            for job in job_cards:
                try:
                    job_id = job.get("data-job-id", "")
                    
                    title_elem = job.select_one(".job-title, h3")
                    company_elem = job.select_one(".company-name, .job-company")
                    location_elem = job.select_one(".job-location, .location")
                    date_elem = job.select_one(".posted-date, .date")
                    
                    title = title_elem.text.strip() if title_elem else ""
                    company = company_elem.text.strip() if company_elem else "Unknown Company"
                    location = location_elem.text.strip() if location_elem else "Remote/Unspecified"
                    date = date_elem.text.strip() if date_elem else "Within 7 days"
                    
                    link = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else ""
                    
                    jobs.append({
                        "title": title,
                        "company": company,
                        "location": location,
                        "date": date,
                        "link": link
                    })
                except Exception as e:
                    print(f"Error extracting job details from alternative card: {e}")
                    continue
        
        return jobs
    
    def search(self, keywords, location, time_period="past-week", max_pages=3, max_jobs=MAX_JOBS_PER_SOURCE):
        """
        Search for jobs on LinkedIn.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            time_period (str): Time period to search for (24h, past-week, etc.)
            max_pages (int): Maximum number of pages to scrape
            max_jobs (int): Maximum number of jobs to return
            
        Returns:
            pd.DataFrame: DataFrame containing job listings
        """
        all_jobs = []
        url = self.build_url(keywords, location, time_period)
        
        print(f"Searching LinkedIn: {url}")
        
        try:
            # First page
            response = requests.get(url, headers=self.get_headers())
            if response.status_code != 200:
                print(f"Failed to get response from LinkedIn: {response.status_code}")
                return self.jobs_df
            
            jobs = self.scrape_jobs_from_html(response.text)
            all_jobs.extend(jobs)
            
            # Process additional pages
            if len(jobs) > 0 and len(all_jobs) < max_jobs and max_pages > 1:
                for page in range(1, min(max_pages, 10)):
                    # LinkedIn pagination
                    start = page * 25  # LinkedIn uses 25 jobs per page
                    page_url = f"{url}&start={start}"
                    
                    # Random delay
                    time.sleep(random.uniform(2, 4))
                    
                    try:
                        response = requests.get(page_url, headers=self.get_headers())
                        if response.status_code == 200:
                            page_jobs = self.scrape_jobs_from_html(response.text)
                            all_jobs.extend(page_jobs)
                            
                            if not page_jobs:
                                # No more jobs found
                                break
                        else:
                            break
                    except Exception as e:
                        print(f"Error fetching page {page}: {e}")
                        break
                    
                    if len(all_jobs) >= max_jobs:
                        break
        
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
        
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
        
        print(f"Found {len(self.jobs_df)} jobs from LinkedIn")
        return self.jobs_df