"""Indeed API and structured scraper for reliable job data."""
import requests
import pandas as pd
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
import json
import re

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class IndeedAPI:
    """
    Indeed API and enhanced structured scraper.
    This combines direct scraping with structured data extraction.
    """
    
    def __init__(self):
        """Initialize the Indeed API."""
        self.name = "Indeed"
        self.base_url = "https://in.indeed.com"
        self.search_url = "https://in.indeed.com/jobs"
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
    
    def build_url(self, keywords, location, days=7):
        """
        Build the URL for Indeed job search.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            days (int): Number of days to look back
            
        Returns:
            str: URL for Indeed job search
        """
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        
        # fromage=7 means jobs posted in the last 7 days
        return f"{self.search_url}?q={encoded_keywords}&l={encoded_location}&fromage={days}&sort=date"
    
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
    
    def scrape_jobs_from_html(self, html):
        """
        Extract job details from Indeed HTML.
        
        Args:
            html (str): HTML content from Indeed search results
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")
        
        # First try structured data
        structured_jobs = self.extract_structured_data(html)
        if structured_jobs:
            return structured_jobs
        
        # Try various selectors for job cards
        job_cards = soup.select("div.job_seen_beacon, div.jobsearch-ResultsList div[data-jk], div.mosaic-provider-jobcards div[data-jk], div[class*='job_seen_beacon']")
        
        for job in job_cards:
            try:
                # Extract job ID
                job_id = job.get("data-jk") or job.get("id", "").replace("job_", "")
                
                # Extract title
                title_elem = job.select_one("h2.jobTitle span, h2.jobTitle a, a.jobtitle, h2 a, h2[class*='jobTitle'] span, h2[class*='jobTitle'] a")
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Extract company
                company_elem = job.select_one("span.companyName, span.company, .companyInfo>span:first-child, [data-testid='company-name']")
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Extract location
                location_elem = job.select_one("div.companyLocation, .location, .outcome, span.location, [data-testid='text-location']")
                location = location_elem.text.strip() if location_elem else "Remote/Unspecified"
                
                # Extract date
                date_elem = job.select_one("span.date, span.date-min, .date, .result-link-bar .date, [class*='date']")
                date = date_elem.text.strip() if date_elem else "Within 7 days"
                
                # Extract link
                link = ""
                if job_id:
                    link = f"https://in.indeed.com/viewjob?jk={job_id}"
                else:
                    link_elem = job.select_one("a[href*='/rc/clk'], a[href*='viewjob'], h2 a, a.jobtitle, a[data-jk]")
                    if link_elem and link_elem.has_attr("href"):
                        href = link_elem["href"]
                        if href.startswith("/"):
                            link = f"https://in.indeed.com{href}"
                        else:
                            link = href
                
                # If still no link, try another method
                if not link:
                    # Try to find any link that might point to the job
                    all_links = job.select("a[href]")
                    for a_tag in all_links:
                        href = a_tag.get('href', '')
                        if "viewjob" in href or "jk=" in href:
                            if href.startswith("/"):
                                link = f"https://in.indeed.com{href}"
                            else:
                                link = href
                            break
                
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
        Search for jobs on Indeed.
        
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
        
        print(f"Searching Indeed: {url}")
        
        try:
            # Process first page
            response = requests.get(url, headers=self.get_headers())
            if response.status_code != 200:
                print(f"Failed to get response from Indeed: {response.status_code}")
                return self.jobs_df
            
            jobs = self.scrape_jobs_from_html(response.text)
            all_jobs.extend(jobs)
            
            # Extract number of results
            soup = BeautifulSoup(response.text, "html.parser")
            count_text = soup.select_one(".jobsearch-JobCountAndSortPane-jobCount span")
            
            if count_text:
                count_str = count_text.text.strip()
                count_match = re.search(r'\d+', count_str)
                if count_match:
                    total_count = int(count_match.group())
                    print(f"Found {total_count} jobs on Indeed")
            
            # Process additional pages if needed
            if len(jobs) > 0 and len(all_jobs) < max_jobs and max_pages > 1:
                # Find pagination links
                for page in range(1, min(max_pages, 10)):  # Indeed typically shows 10 pages max
                    # Calculate start parameter (10 jobs per page)
                    start = page * 10
                    page_url = f"{url}&start={start}"
                    
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(2, 4))
                    
                    try:
                        response = requests.get(page_url, headers=self.get_headers())
                        if response.status_code == 200:
                            page_jobs = self.scrape_jobs_from_html(response.text)
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
            print(f"Error searching Indeed: {e}")
        
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
        
        print(f"Found {len(self.jobs_df)} jobs from Indeed")
        return self.jobs_df