"""Naukri job scraper."""
import urllib.parse
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from scrapers.base_scraper import BaseScraper
from config.config import MAX_JOBS_PER_SOURCE


class NaukriScraper(BaseScraper):
    """Scraper for Naukri job listings."""
    
    def __init__(self):
        """Initialize the Naukri scraper."""
        super().__init__("Naukri")
    
    def build_url(self, keywords, location):
        """Build the URL for Naukri job search."""
        encoded_keywords = urllib.parse.quote_plus(keywords)
        encoded_location = urllib.parse.quote_plus(location)
        return f"https://www.naukri.com/jobs-in-{encoded_location}?keywordsearch={encoded_keywords}&experience=0&nignbevent_src=jobsearchDesk&jobAge=1"
    
    def scrape(self, keywords, location, max_jobs=MAX_JOBS_PER_SOURCE):
        """Scrape Naukri for jobs matching the keywords and location."""
        url = self.build_url(keywords, location)
        
        # Naukri requires Selenium due to its dynamic content
        driver = self.setup_selenium()
        
        if not driver:
            print("Failed to set up Selenium for Naukri")
            return self.jobs_df
        
        try:
            driver.get(url)
            
            # Wait for job listings to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".jobTuple, .srp-jobtuple-wrapper, .cust-job-tuple"))
                )
            except TimeoutException:
                print("Timeout waiting for Naukri jobs to load")
            
            # Scroll down to load more results (Naukri uses lazy loading)
            for _ in range(2):  # Scroll a few times to load more jobs
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            # Extract job listings with multiple selector options
            job_elements = driver.find_elements(By.CSS_SELECTOR, 
                ".jobTuple, .srp-jobtuple-wrapper, .cust-job-tuple")
            
            job_count = 0
            for job in job_elements[:max_jobs]:
                try:
                    title_elem = job.find_element(By.CSS_SELECTOR, 
                        ".title, .title a, .designation")
                    company_elem = job.find_element(By.CSS_SELECTOR, 
                        ".companyInfo, .comp-name")
                    location_elem = job.find_element(By.CSS_SELECTOR, 
                        ".location, .loc, .ellipsis.fleft.locWdth")
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip().split("\n")[0]
                    location = location_elem.text.strip()
                    
                    # Try to find the date from various elements
                    date = "Today"
                    try:
                        date_elem = job.find_element(By.CSS_SELECTOR, ".jobAge, .exp")
                        date_text = date_elem.text.strip()
                        if date_text:
                            date = date_text
                    except NoSuchElementException:
                        pass
                    
                    # Get the job link
                    try:
                        link_elem = job.find_element(By.CSS_SELECTOR, ".title a, a")
                        link = link_elem.get_attribute("href")
                    except NoSuchElementException:
                        link = url
                    
                    self.add_job(title, company, location, date, link)
                    job_count += 1
                    
                except Exception as e:
                    print(f"Error extracting job details from Naukri: {e}")
                    continue
            
            print(f"Scraped {job_count} jobs from Naukri for {keywords} in {location}")
            
        except Exception as e:
            print(f"Error scraping Naukri: {e}")
        
        finally:
            driver.quit()
            
        return self.jobs_df