"""Scraper for company career pages."""
import time
import re
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from config.config import COMPANY_CAREER_PAGES, MAX_JOBS_PER_SOURCE


class CompanyCareerScraper(BaseScraper):
    """Scraper for company career pages."""
    
    def __init__(self, company_config):
        """
        Initialize the company career page scraper.
        
        Args:
            company_config (dict): Dictionary with company configuration
                                  (name, url, dynamic).
        """
        super().__init__(company_config["name"])
        self.url = company_config["url"]
        self.dynamic = company_config["dynamic"]
    
    def is_recent_job(self, date_str, days=7):
        """
        Check if a job posting is within the specified days.
        
        Args:
            date_str (str): Date string to check
            days (int): Number of days to consider as recent
            
        Returns:
            bool: True if the job is recent, False otherwise
        """
        # Common patterns for recent jobs
        recent_patterns = [
            'today', 'just now', 'hours ago', 'hour ago', 'minutes ago',
            'yesterday', 'day ago', 'days ago', 'week ago', 'new',
            'recently', 'posted today', 'recently posted'
        ]
        
        # Check if any pattern matches
        date_lower = date_str.lower()
        if any(pattern in date_lower for pattern in recent_patterns):
            # Check if it specifically mentions days and the number is more than our limit
            days_match = re.search(r'(\d+)\s*days?\s*ago', date_lower)
            if days_match:
                days_ago = int(days_match.group(1))
                return days_ago <= days
            return True
        
        # Try to parse date strings in various formats
        try:
            # Common format patterns
            formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%B %d, %Y',
                '%b %d, %Y', '%d %B %Y', '%d %b %Y'
            ]
            
            for fmt in formats:
                try:
                    job_date = datetime.strptime(date_str, fmt)
                    # Check if within the days limit
                    return (datetime.now() - job_date).days <= days
                except ValueError:
                    continue
        except:
            # If we can't determine, assume it's recent
            return True
        
        # Default to including the job
        return True
    
    def scrape(self, keywords, location, max_jobs=MAX_JOBS_PER_SOURCE, days=7):
        """
        Scrape the company career page for jobs matching the keywords.
        
        Args:
            keywords (str): Keywords to filter jobs by.
            location (str): Location to filter jobs by (ignored as URL already has location).
            max_jobs (int): Maximum number of jobs to scrape.
            days (int): Number of days to consider as recent jobs.
        
        Returns:
            pd.DataFrame: Dataframe with the scraped jobs.
        """
        keyword_list = keywords.lower().split()
        
        if self.dynamic:
            return self._scrape_dynamic(keyword_list, max_jobs, days)
        else:
            return self._scrape_static(keyword_list, max_jobs, days)
    
    def _scrape_static(self, keyword_list, max_jobs, days):
        """Scrape static HTML career pages."""
        html = self.make_request(self.url)
        
        if not html:
            print(f"Failed to get response from {self.name} career page")
            return self.jobs_df
        
        soup = BeautifulSoup(html, "html.parser")
        
        # Since each company page has a different structure, we'll try different common selectors
        job_cards = soup.select(".job-card, .job-listing, .job-item, .jobsearch-SerpJobCard")
        
        job_count = 0
        for job in job_cards:
            if job_count >= max_jobs:
                break
            
            try:
                # Try different common selectors for job details
                title_elem = job.select_one(".job-title, .title, h2, h3")
                company_elem = job.select_one(".company-name, .company, .employer")
                location_elem = job.select_one(".location, .job-location")
                date_elem = job.select_one(".date, .posted-date, .job-date")
                
                if not title_elem:
                    continue
                
                title = title_elem.text.strip()
                
                # Check if any keyword matches the job title
                if not any(keyword in title.lower() for keyword in keyword_list):
                    continue
                
                company = company_elem.text.strip() if company_elem else self.name
                location = location_elem.text.strip() if location_elem else "Bengaluru"
                date = date_elem.text.strip() if date_elem else "Recent"
                
                # Check if the job is recent
                if not self.is_recent_job(date, days):
                    continue
                
                # Extract link
                link = ""
                if link_elem := job.select_one("a"):
                    if link_elem.has_attr("href"):
                        href = link_elem["href"]
                        if href.startswith("/"):
                            # Relative URL
                            base_url = "/".join(self.url.split("/")[:3])  # Get domain
                            link = f"{base_url}{href}"
                        else:
                            link = href
                
                self.add_job(title, company, location, date, link)
                job_count += 1
            
            except Exception as e:
                print(f"Error extracting job details from {self.name}: {e}")
                continue
        
        print(f"Scraped {job_count} jobs from {self.name} career page")
        return self.jobs_df
    
    def _scrape_dynamic(self, keyword_list, max_jobs, days):
        """Scrape dynamically loaded career pages using Selenium."""
        driver = self.setup_selenium()
        
        if not driver:
            print(f"Failed to set up Selenium for {self.name}")
            return self.jobs_df
        
        try:
            driver.get(self.url)
            
            # Wait for page to load (looking for common job listing containers)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 
                        ".job-card, .job-listing, .job-item, div[data-automation-id='jobTitle'], .jobs-search-results__list-item"
                    ))
                )
            except TimeoutException:
                print(f"Timeout waiting for {self.name} career page to load")
            
            # Allow more time for dynamic content to load
            time.sleep(3)
            
            # Try different selectors based on common patterns in career sites
            selectors = [
                # Common career page selectors
                {"jobs": ".job-card, .job-listing, .job-item, .jobs-search-results__list-item",
                 "title": ".job-title, .title, h2, h3, a[data-automation-id='jobTitle']",
                 "company": ".company-name, .company, .employer",
                 "location": ".location, .job-location, span[data-automation-id='locationLabel']",
                 "date": ".date, .posted-date, .job-date",
                 "link": "a"},
                
                # JPMorgan specific
                {"jobs": ".job-card, .jobDetailRow",
                 "title": ".jobTitle, .job-title",
                 "company": ".company",
                 "location": ".location, .job-location",
                 "date": ".posted-date",
                 "link": "a"},
                
                # Workday specific (State Street, etc.)
                {"jobs": "[data-automation-id='jobResult']",
                 "title": "[data-automation-id='jobTitle']",
                 "location": "[data-automation-id='locationLabel']",
                 "date": "[data-automation-id='postedOn']",
                 "link": "a"},
                
                # Goldman Sachs specific
                {"jobs": ".job-tile",
                 "title": ".job-tile-title",
                 "location": ".job-tile-location",
                 "date": ".job-tile-date",
                 "link": "a"}
            ]
            
            job_count = 0
            
            # Try each selector pattern
            for selector_set in selectors:
                try:
                    job_elements = driver.find_elements(By.CSS_SELECTOR, selector_set["jobs"])
                    
                    if job_elements:
                        for job in job_elements[:max_jobs]:
                            try:
                                # Try to extract job details using current selector pattern
                                title_elem = job.find_element(By.CSS_SELECTOR, selector_set["title"])
                                title = title_elem.text.strip()
                                
                                # Check if any keyword matches the job title
                                if not any(keyword in title.lower() for keyword in keyword_list):
                                    continue
                                
                                # Extract other details
                                try:
                                    company_selector = selector_set.get("company")
                                    company = job.find_element(By.CSS_SELECTOR, company_selector).text.strip() if company_selector else self.name
                                except NoSuchElementException:
                                    company = self.name
                                    
                                try:
                                    location_selector = selector_set.get("location")
                                    location = job.find_element(By.CSS_SELECTOR, location_selector).text.strip() if location_selector else "Bengaluru"
                                except NoSuchElementException:
                                    location = "Bengaluru"
                                    
                                try:
                                    date_selector = selector_set.get("date")
                                    date = job.find_element(By.CSS_SELECTOR, date_selector).text.strip() if date_selector else "Recent"
                                except NoSuchElementException:
                                    date = "Recent"
                                
                                # Check if the job is recent
                                if not self.is_recent_job(date, days):
                                    continue
                                
                                # Extract link
                                try:
                                    link_elem = job.find_element(By.CSS_SELECTOR, selector_set["link"])
                                    link = link_elem.get_attribute("href")
                                    
                                    # Ensure link is valid
                                    if not link or not (link.startswith("http") or link.startswith("https")):
                                        # Try alternative link finding
                                        all_links = job.find_elements(By.TAG_NAME, "a")
                                        for a in all_links:
                                            href = a.get_attribute("href")
                                            if href and (href.startswith("http") or href.startswith("https")):
                                                link = href
                                                break
                                except NoSuchElementException:
                                    link = ""
                                
                                self.add_job(title, company, location, date, link)
                                job_count += 1
                                
                                if job_count >= max_jobs:
                                    break
                                    
                            except Exception as e:
                                print(f"Error extracting job details from {self.name}: {e}")
                                continue
                        
                        # If we found and processed jobs with this selector pattern, no need to try others
                        if job_count > 0:
                            break
                            
                except Exception as e:
                    print(f"Error with selector pattern for {self.name}: {e}")
                    continue
            
            print(f"Scraped {job_count} jobs from {self.name} career page")
            
        except Exception as e:
            print(f"Error scraping {self.name} career page: {e}")
        
        finally:
            driver.quit()
            
        return self.jobs_df


def get_company_scrapers():
    """Return a list of scrapers for all configured company career pages."""
    return [CompanyCareerScraper(company) for company in COMPANY_CAREER_PAGES]