"""Indeed job scraper."""
import urllib.parse
from bs4 import BeautifulSoup
import pandas as pd

from scrapers.base_scraper import BaseScraper
from config.config import MAX_JOBS_PER_SOURCE


class IndeedScraper(BaseScraper):
    """Scraper for Indeed job listings."""
    
    def __init__(self):
        """Initialize the Indeed scraper."""
        super().__init__("Indeed")
    
    def build_url(self, keywords, location, days=7):
        """Build the URL for Indeed job search."""
        encoded_keywords = urllib.parse.quote_plus(keywords)
        encoded_location = urllib.parse.quote_plus(location)
        return f"https://in.indeed.com/jobs?q={encoded_keywords}&l={encoded_location}&fromage={days}"
    
    def scrape(self, keywords, location, max_jobs=MAX_JOBS_PER_SOURCE, days=7):
        """Scrape Indeed for jobs matching the keywords and location."""
        url = self.build_url(keywords, location, days)
        html = self.make_request(url)
        
        if not html:
            print(f"Failed to get response from Indeed for {keywords} in {location}")
            return self.jobs_df
        
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.select("div.job_seen_beacon, div.jobsearch-SerpJobCard")
        
        job_count = 0
        for job in job_cards:
            if job_count >= max_jobs:
                break
                
            try:
                # Extract job details with multiple selector options
                title_elem = job.select_one("h2.jobTitle span, h2.jobTitle a, .title")
                company_elem = job.select_one("span.companyName, span.company, .companyName")
                location_elem = job.select_one("div.companyLocation, .location, div.location")
                date_elem = job.select_one("span.date, .date, span.post-date")
                
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                company = company_elem.text.strip() if company_elem else "Unknown Company"
                location = location_elem.text.strip() if location_elem else location
                date = date_elem.text.strip() if date_elem else "Recently posted"
                
                # Extract job link
                link_elem = job.select_one("h2.jobTitle a, a[href*='viewjob']")
                link = ""
                if link_elem and link_elem.has_attr("href"):
                    href = link_elem["href"]
                    if href.startswith("/"):
                        link = f"https://in.indeed.com{href}"
                    else:
                        link = href
                
                # Add job to dataframe
                self.add_job(title, company, location, date, link)
                job_count += 1
                
            except Exception as e:
                print(f"Error extracting job details from Indeed: {e}")
                continue
        
        print(f"Scraped {job_count} jobs from Indeed for {keywords} in {location}")
        return self.jobs_df