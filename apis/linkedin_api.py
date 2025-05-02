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
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "DNT": "1"
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
        
        # Use geoId for better location targeting
        geo_id = "4046"  # ID for Bangalore - this improves location targeting
        geo_param = f"&geoId={geo_id}" if "bangalore" in location.lower() or "bengaluru" in location.lower() else ""
        
        return f"{self.search_url}/?keywords={encoded_keywords}&location={encoded_location}{time_param}{geo_param}&sortBy=DD&position=1&pageNum=0"
    
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
    
    def extract_job_data_from_script(self, html):
        """
        Extract job data from embedded script data.
        
        Args:
            html (str): HTML content
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        
        try:
            # Look for initial state data in script tags
            soup = BeautifulSoup(html, "html.parser")
            
            # Look for the job data in the HTML
            job_data_pattern = re.compile(r'window\.INITIAL_STATE\s*=\s*({.*?});\s*</script>', re.DOTALL)
            script_content = re.search(job_data_pattern, html)
            
            if script_content:
                try:
                    # Extract the JSON data
                    json_text = script_content.group(1)
                    data = json.loads(json_text)
                    
                    # Navigate through the LinkedIn data structure to find jobs
                    if 'entityUrn' in str(data):
                        # Search for jobs in the data
                        for key, value in data.items():
                            if isinstance(value, dict) and 'included' in value:
                                included = value.get('included', [])
                                for item in included:
                                    if isinstance(item, dict) and 'title' in item and 'companyName' in item:
                                        title = item.get('title', '')
                                        company = item.get('companyName', '')
                                        location = item.get('formattedLocation', '')
                                        
                                        # Get link
                                        entity_urn = item.get('entityUrn', '')
                                        job_id = entity_urn.split(':')[-1] if entity_urn else ''
                                        link = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else ""
                                        
                                        # Get date
                                        listed_at = item.get('listedAt', 0)
                                        if listed_at:
                                            # Convert timestamp to days ago
                                            import time
                                            now = int(time.time() * 1000)  # LinkedIn uses milliseconds
                                            days_ago = int((now - listed_at) / (24 * 60 * 60 * 1000))
                                            date = f"{days_ago} days ago" if days_ago > 0 else "Today"
                                        else:
                                            date = "Recently posted"
                                        
                                        job = {
                                            "title": title,
                                            "company": company,
                                            "location": location,
                                            "date": date,
                                            "link": link
                                        }
                                        jobs.append(job)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"Error extracting job data from script: {e}")
        
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
        
        # First try structured data
        structured_jobs = self.extract_structured_data(html)
        if structured_jobs:
            return structured_jobs
        
        # Then try to extract from script data
        script_jobs = self.extract_job_data_from_script(html)
        if script_jobs:
            return script_jobs
        
        # Try different selectors for job cards
        job_cards = soup.select(".jobs-search__results-list li, .job-search-card, .base-card")
        
        if not job_cards:
            # Try alternatives for newer LinkedIn layouts
            job_cards = soup.select("[data-job-id], .job-card-container, [data-entity-urn*='jobPosting']")
        
        for job in job_cards:
            try:
                # Title and link
                title_elem = job.select_one(".base-search-card__title, .job-search-card__title, .base-card__full-link, .job-card-container__link, h3")
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Link could be in the title element or a parent
                link_elem = title_elem if title_elem.name == "a" else job.select_one("a.base-card__full-link, a.job-search-card__link, a[href*='jobs/view']")
                link = ""
                if link_elem and link_elem.has_attr("href"):
                    href = link_elem["href"]
                    if href.startswith("/"):
                        link = urljoin(self.base_url, href)
                    else:
                        link = href
                
                # Get job ID as fallback for link
                job_id = None
                if not link:
                    # Try to extract job ID from data attributes
                    if job.has_attr("data-job-id"):
                        job_id = job["data-job-id"]
                    elif job.has_attr("data-entity-urn"):
                        urn = job["data-entity-urn"]
                        job_id = urn.split(":")[-1] if ":" in urn else None
                    
                    # Create link from job ID
                    if job_id:
                        link = f"https://www.linkedin.com/jobs/view/{job_id}/"
                
                # Company
                company_elem = job.select_one(".base-search-card__subtitle, .job-search-card__subtitle a, .base-card__metadata a:first-child, .job-card-container__company-name")
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                
                # Location
                location_elem = job.select_one(".job-search-card__location, span.job-search-card__location, .base-card__metadata span.job-search-card__location, .job-card-container__metadata-item")
                location = location_elem.text.strip() if location_elem else "Remote/Unspecified"
                
                # Date - look for a time element
                date_elem = job.select_one("time, .job-search-card__listdate, .base-card__metadata time, .job-card-container__footer-item")
                date = date_elem.text.strip() if date_elem and date_elem.text.strip() else "Within 7 days"
                
                # Ensure we have a link before adding the job
                if link:
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
            # First page with specific User-Agent rotation
            headers = self.get_headers()
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"Failed to get response from LinkedIn: {response.status_code}")
                return self.jobs_df
            
            jobs = self.scrape_jobs_from_html(response.text)
            all_jobs.extend(jobs)
            
            # Process additional pages
            if len(jobs) > 0 and len(all_jobs) < max_jobs and max_pages > 1:
                for page in range(1, min(max_pages, 10)):
                    # LinkedIn pagination - rotate user agents to avoid detection
                    user_agents = [
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
                    ]
                    
                    headers = self.get_headers()
                    headers["User-Agent"] = random.choice(user_agents)
                    
                    # LinkedIn uses pageNum parameter
                    page_url = f"{self.search_url}/?keywords={quote_plus(keywords)}&location={quote_plus(location)}&f_TPR=r604800&pageNum={page}"
                    
                    # Random delay with jitter to avoid detection
                    time.sleep(random.uniform(2, 4))
                    
                    try:
                        response = requests.get(page_url, headers=headers, timeout=15)
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
            
            # If we still have no jobs, try a different approach
            if not all_jobs:
                print("Trying alternative LinkedIn search method...")
                alt_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote_plus(keywords)}&location={quote_plus(location)}&trk=public_jobs_jobs-search-bar_search-submit&f_TPR=r604800&start=0"
                
                headers = self.get_headers()
                headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                
                response = requests.get(alt_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    jobs = self.scrape_jobs_from_html(response.text)
                    all_jobs.extend(jobs)
        
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
        
        # Convert to DataFrame - ensure links are valid
        for job in all_jobs[:max_jobs]:
            # Clean the link to ensure it's direct
            link = job.get("link", "")
            if "linkedin.com" in link and "/jobs/view/" not in link:
                # Try to extract job ID and recreate link
                job_id = re.search(r'currentJobId=([0-9]+)', link)
                if job_id:
                    link = f"https://www.linkedin.com/jobs/view/{job_id.group(1)}/"
            
            self.jobs_df = pd.concat([
                self.jobs_df,
                pd.DataFrame({
                    "title": [job["title"]],
                    "company": [job["company"]],
                    "location": [job["location"]],
                    "date": [job["date"]],
                    "link": [link],
                    "source": [self.name]
                })
            ], ignore_index=True)
        
        print(f"Found {len(self.jobs_df)} jobs from LinkedIn")
        return self.jobs_df