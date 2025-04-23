"""Foundit (formerly Monster) job scraper."""
import urllib.parse
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from scrapers.base_scraper import BaseScraper
from config.config import MAX_JOBS_PER_SOURCE


class FounditScraper(BaseScraper):
    """Scraper for Foundit (formerly Monster) job listings."""
    
    def __init__(self):
        """Initialize the Foundit scraper."""
        super().__init__("Foundit")
    
    def build_url(self, keywords, location):
        """Build the URL for Foundit job search."""
        encoded_keywords = urllib.parse.quote_plus(keywords)
        encoded_location = urllib.parse.quote_plus(location)
        return f"https://www.foundit.in/srp/results?keyword={encoded_keywords}&location={encoded_location}&sort=0&flow=default&experienceMin=0&experienceMax=30&postDate=1"
    
    def scrape(self, keywords, location, max_jobs=MAX_JOBS_PER_SOURCE):
        """Scrape Foundit for jobs matching the keywords and location."""
        url = self.build_url(keywords, location)
        
        # Foundit requires Selenium due to its dynamic content
        driver = self.setup_selenium()
        
        if not driver:
            print("Failed to set up Selenium for Foundit")
            return self.jobs_df
        
        try:
            driver.get(url)
            
            # Wait for job listings to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".card-apply-content, .srpRightPart"))
                )
            except TimeoutException:
                print("Timeout waiting for Foundit jobs to load")
            
            # Scroll down to load more results
            for _ in range(2):  # Scroll a few times to load more jobs
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
            
            # Extract job listings
            job_cards = driver.find_elements(By.CSS_SELECTOR, ".card-apply-content, .srpRightPart")
            
            job_count = 0
            for job in job_cards[:max_jobs]:
                try:
                    title_elem = job.find_element(By.CSS_SELECTOR, ".job-tittle a, .jobTitle a")
                    company_elem = job.find_element(By.CSS_SELECTOR, ".company-name a, .companyName a")
                    location_elem = job.find_element(By.CSS_SELECTOR, ".loc span, .jobLocation span")
                    
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    location = location_elem.text.strip()
                    
                    # Get the date if available
                    date = "Recently posted"
                    try:
                        date_elem = job.find_element(By.CSS_SELECTOR, ".posted-update span, .posted-date")
                        date = date_elem.text.strip()
                    except NoSuchElementException:
                        pass
                    
                    # Get the job link
                    link = title_elem.get_attribute("href")
                    
                    self.add_job(title, company, location, date, link)
                    job_count += 1
                    
                except Exception as e:
                    print(f"Error extracting job details from Foundit: {e}")
                    continue
            
            print(f"Scraped {job_count} jobs from Foundit for {keywords} in {location}")
            
        except Exception as e:
            print(f"Error scraping Foundit: {e}")
        
        finally:
            driver.quit()
            
        return self.jobs_df