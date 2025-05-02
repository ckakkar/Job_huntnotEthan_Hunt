"""Direct HTML scraper for job sites - fallback to OpenAI scraper."""
import requests
import pandas as pd
import time
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class DirectScraper:
    """
    Direct HTML scraper for job sites.
    Uses various fallback methods to extract job listings without relying on OpenAI.
    """
    
    def __init__(self, name, url_template):
        """
        Initialize the direct HTML scraper.
        
        Args:
            name (str): Name of the job site
            url_template (str): URL template with {keywords} and {location} placeholders
        """
        self.name = name
        self.url_template = url_template
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
    
    def build_url(self, keywords, location):
        """Build the URL for the job search."""
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        return self.url_template.format(keywords=encoded_keywords, location=encoded_location)
    
    def extract_jobs_using_selectors(self, soup, aggressive=False):
        """
        Extract jobs from HTML using site-specific selectors.
        
        Args:
            soup (BeautifulSoup): BeautifulSoup object of the HTML
            aggressive (bool): Whether to use more aggressive selectors
            
        Returns:
            list: List of job dictionaries
        """
        jobs = []
        
        # Define selectors based on site name
        selectors = self.get_site_selectors(aggressive)
        
        # Find job containers using all possible selectors
        job_containers = []
        for container_selector in selectors["job_containers"]:
            containers = soup.select(container_selector)
            if containers:
                job_containers.extend(containers)
                if not aggressive:
                    break
        
        # Process each job container
        for container in job_containers:
            try:
                job = {}
                
                # Extract title
                for selector in selectors["title"]:
                    title_elem = container.select_one(selector)
                    if title_elem:
                        job["title"] = title_elem.text.strip()
                        break
                
                # Skip if no title found
                if "title" not in job or not job["title"]:
                    continue
                
                # Extract company
                for selector in selectors["company"]:
                    company_elem = container.select_one(selector)
                    if company_elem:
                        job["company"] = company_elem.text.strip()
                        break
                
                if "company" not in job or not job["company"]:
                    job["company"] = self.name
                
                # Extract location
                for selector in selectors["location"]:
                    location_elem = container.select_one(selector)
                    if location_elem:
                        job["location"] = location_elem.text.strip()
                        break
                
                if "location" not in job or not job["location"]:
                    job["location"] = "Bangalore"
                
                # Extract date
                for selector in selectors["date"]:
                    date_elem = container.select_one(selector)
                    if date_elem:
                        job["date"] = date_elem.text.strip()
                        break
                
                if "date" not in job or not job["date"]:
                    job["date"] = "Recent"
                
                # Extract link
                job["link"] = ""
                # First try title link
                for selector in selectors["title_link"]:
                    link_elem = container.select_one(selector)
                    if link_elem and link_elem.has_attr("href"):
                        href = link_elem["href"]
                        if href.startswith("http"):
                            job["link"] = href
                        else:
                            # Convert relative URLs to absolute
                            base_url = "/".join(self.url_template.split("/")[:3])
                            job["link"] = urljoin(base_url, href)
                        break
                
                # If no link found, try generic link selectors
                if not job["link"]:
                    for selector in selectors["link"]:
                        link_elem = container.select_one(selector)
                        if link_elem and link_elem.has_attr("href"):
                            href = link_elem["href"]
                            if href.startswith("http"):
                                job["link"] = href
                            else:
                                base_url = "/".join(self.url_template.split("/")[:3])
                                job["link"] = urljoin(base_url, href)
                            break
                
                # If still no link, try to find any link in the container
                if not job["link"] and aggressive:
                    all_links = container.select("a[href]")
                    for link in all_links:
                        if link.has_attr("href"):
                            href = link["href"]
                            if href.startswith("http"):
                                job["link"] = href
                            else:
                                base_url = "/".join(self.url_template.split("/")[:3])
                                job["link"] = urljoin(base_url, href)
                            break
                
                # Add to jobs list if we have at least title and company
                if job.get("title") and job.get("company"):
                    jobs.append(job)
            except Exception as e:
                print(f"Error extracting job from container: {e}")
                continue
        
        return jobs
    
    def get_site_selectors(self, aggressive=False):
        """
        Get selectors for a specific site.
        
        Args:
            aggressive (bool): Whether to use more aggressive selectors
            
        Returns:
            dict: Dictionary of selectors
        """
        # Default selectors that work with many sites
        default_selectors = {
            "job_containers": [
                ".job-card", ".job-listing", ".job-search-card", 
                ".jobs-search-results__list-item", "[data-job-id]"
            ],
            "title": [
                ".job-title", ".title", "h2 a", "h3 a", "[data-automation-id='jobTitle']", 
                ".base-search-card__title", ".job-search-card__title"
            ],
            "company": [
                ".company-name", ".company", "[data-automation-id='companyName']",
                ".base-search-card__subtitle", ".job-search-card__subtitle"
            ],
            "location": [
                ".location", ".job-location", "[data-automation-id='locationLabel']",
                ".base-search-card__metadata", ".job-search-card__location"
            ],
            "date": [
                ".date", ".posted-date", ".job-date", "[data-automation-id='postedDate']",
                "time", ".job-search-card__listdate"
            ],
            "title_link": [
                "h2 a", "h3 a", ".job-title a", ".title a", "[data-automation-id='jobTitle']"
            ],
            "link": ["a.job-card-container__link", "a.base-card__full-link", "a[href*='job']"]
        }
        
        # Site-specific selectors
        site_selectors = {
            "LinkedIn": {
                "job_containers": [".jobs-search-results__list-item", ".job-search-card", ".base-card"],
                "title": [".base-search-card__title", ".job-search-card__title", "h3"],
                "company": [".base-search-card__subtitle", ".job-search-card__subtitle", "h4"],
                "location": [".job-search-card__location", ".base-search-card__metadata", ".job-card-container__metadata-item"],
                "date": ["time", ".job-search-card__listdate", ".job-card-container__footer-item"],
                "title_link": [".base-card__full-link", ".job-card-container__link", "h3 a"],
                "link": ["a.base-card__full-link", "a.job-card-container__link", "a[href*='jobs/view']"]
            },
            "Indeed": {
                "job_containers": [".job_seen_beacon", ".jobsearch-ResultsList div[data-jk]", ".mosaic-provider-jobcards div[data-jk]"],
                "title": ["h2.jobTitle span", "h2.jobTitle a", "a.jobtitle"],
                "company": ["span.companyName", "span.company", ".companyInfo>span"],
                "location": ["div.companyLocation", ".location", ".recJobLoc"],
                "date": ["span.date", ".result-link-bar .date", "[class*='date']"],
                "title_link": ["h2 a", "a.jobtitle", "a[data-jk]"],
                "link": ["a[href*='/rc/clk']", "a[href*='viewjob']", "a[data-jk]"]
            },
            "Naukri": {
                "job_containers": [".jobTuple", ".srp-jobtuple-wrapper", ".job-tuple"],
                "title": [".title", ".title a", ".designation"],
                "company": [".companyInfo", ".comp-name", ".org"],
                "location": [".location", ".loc", ".ellipsis.fleft.locWdth"],
                "date": [".jobDate", ".date", ".fleft.postedDate"],
                "title_link": [".title a", ".jobTupleHeader a"],
                "link": ["a.title", "a[href*='job-listings']"]
            },
            "Foundit": {
                "job_containers": [".card-apply-content", ".srpRightPart", ".job-wraper"],
                "title": [".job-tittle", ".jobTitle", ".card-title"],
                "company": [".company-name", ".companyName", ".company-dtl"],
                "location": [".loc span", ".jobLocation", ".loc-span"],
                "date": [".posted-update", ".posted-date", ".time-stamp"],
                "title_link": [".job-tittle a", ".jobTitle a"],
                "link": ["a[href*='job-detail']", "a[href*='monster.com']"]
            }
        }
        
        # Add additional company-specific selectors
        company_selectors = {
            "JPMorgan": {
                "job_containers": [".job-result-tile", "[data-automation-id='jobCard']"],
                "title": [".job-result-title", "[data-automation-id='jobTitle']"],
                "company": [".job-result-company", "[data-automation-id='companyName']"],
                "location": [".job-result-location", "[data-automation-id='jobLocation']"],
                "date": [".job-result-posted-date", "[data-automation-id='postedDate']"],
                "title_link": [".job-result-title a", "a[data-automation-id='jobTitle']"],
                "link": ["a[href*='job-detail']", "a[href*='jobs/job']"]
            },
            "Goldman Sachs": {
                "job_containers": [".job-tile", ".job-card", ".job-listing"],
                "title": [".job-tile-title", ".job-title", "h3"],
                "company": [".job-tile-company", ".company-name"],
                "location": [".job-tile-location", ".location"],
                "date": [".job-tile-date", ".date"],
                "title_link": [".job-tile-title a", "h3 a"],
                "link": ["a[href*='careers']"]
            }
        }
        
        # Get selectors for this site, with fallback to default
        selectors = site_selectors.get(self.name, company_selectors.get(self.name, default_selectors))
        
        # If aggressive mode, add more selectors
        if aggressive:
            selectors["job_containers"].extend([
                "div[class*='job']", "div[class*='card']", "li", "article",
                "div.row", "div.col", "div[role='article']", "div[role='listitem']"
            ])
            selectors["title"].extend([
                "h1", "h2", "h3", "h4", "strong", "b", "[class*='title']", "span[class*='title']"
            ])
            selectors["company"].extend([
                "[class*='company']", "p", "span", "div[class*='company']"
            ])
            selectors["location"].extend([
                "[class*='loc']", "address", "span", "p", "div[class*='loc']"
            ])
            selectors["link"].extend([
                "a", "a[href]", "a[href*='job']", "a[href*='career']"
            ])
        
        return selectors
    
    def scrape(self, keywords, location, max_jobs=MAX_JOBS_PER_SOURCE, aggressive=False):
        """
        Scrape jobs from the website using direct HTML parsing.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            max_jobs (int): Maximum number of jobs to scrape
            aggressive (bool): Whether to use aggressive extraction
            
        Returns:
            pd.DataFrame: DataFrame containing the scraped job listings
        """
        url = self.build_url(keywords, location)
        print(f"Scraping {self.name} using direct HTML parsing...")
        
        # Use different User-Agents to avoid blocking
        headers = self.get_headers()
        
        try:
            # Make request
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code} from {self.name}")
                return self.jobs_df
            
            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract jobs using selectors
            jobs = self.extract_jobs_using_selectors(soup, aggressive)
            
            # Process jobs
            for job in jobs[:max_jobs]:
                try:
                    # Check if the job title contains any of the keywords
                    if not aggressive and keywords and not any(kw.lower() in job["title"].lower() for kw in keywords.split()):
                        continue
                    
                    # Check location relevance for non-aggressive mode
                    if not aggressive and job["location"] and "bangalore" not in job["location"].lower() and "bengaluru" not in job["location"].lower() and "remote" not in job["location"].lower():
                        continue
                    
                    # Add to dataframe
                    job_data = pd.DataFrame({
                        "title": [job["title"]],
                        "company": [job["company"]],
                        "location": [job["location"]],
                        "date": [job["date"]],
                        "link": [job["link"]],
                        "source": [self.name]
                    })
                    
                    self.jobs_df = pd.concat([self.jobs_df, job_data], ignore_index=True)
                    
                except Exception as e:
                    print(f"Error processing job from {self.name}: {e}")
                    continue
            
            print(f"Found {len(self.jobs_df)} jobs from {self.name} using direct HTML parsing")
            
        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
        
        return self.jobs_df