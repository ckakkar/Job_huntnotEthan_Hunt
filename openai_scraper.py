"""OpenAI-powered job scraper optimized for cost-efficiency."""
import requests
import json
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote_plus

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class OpenAIScraper:
    """
    A job scraper that uses OpenAI to extract structured job data from HTML.
    This avoids the need for Selenium by using AI to parse job listings.
    Optimized to use the cheapest OpenAI model (gpt-3.5-turbo).
    """
    
    def __init__(self, name, url_template, api_key=None):
        """
        Initialize the OpenAI-powered scraper.
        
        Args:
            name (str): Name of the job site
            url_template (str): URL template with {keywords} and {location} placeholders
            api_key (str, optional): OpenAI API key. If not provided, will try to get from env
        """
        self.name = name
        self.url_template = url_template
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.jobs_df = pd.DataFrame(columns=["title", "company", "location", "date", "link", "source"])
    
    def get_headers(self):
        """Return the headers to use for requests."""
        return {
            "User-Agent": USER_AGENT
        }
    
    def build_url(self, keywords, location):
        """Build the URL for the job search."""
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        return self.url_template.format(keywords=encoded_keywords, location=encoded_location)
    
    def extract_jobs_with_openai(self, html_content):
        """
        Extract job listings from HTML content using OpenAI.
        
        Args:
            html_content (str): HTML content of the job listings page
            
        Returns:
            list: List of dictionaries containing job details
        """
        if not self.api_key:
            print(f"OpenAI API key required for {self.name} scraper")
            return []
        
        try:
            # Parse the HTML to text
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Remove script and style tags to clean up text
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text content
            text = soup.get_text(separator=" ", strip=True)
            
            # Truncate to fit GPT-3.5's context
            max_chars = 4000
            text = text[:max_chars]
            
            # Simple prompt
            prompt = f"Extract job listings from this webpage text as a JSON array. Each job should have title, company, location, date, and link fields. Keep it minimal.\n\nText: {text}"
            
            # Call OpenAI API
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "Extract job listings as structured JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                print(f"Error from OpenAI API: {response.status_code}")
                return []
            
            # Parse response
            result = response.json()
            
            # Extract content
            if "choices" not in result or not result["choices"]:
                return []
                
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON
            try:
                # Find JSON array pattern if needed
                import re
                json_pattern = re.compile(r'\[\s*\{.*\}\s*\]', re.DOTALL)
                match = json_pattern.search(content)
                
                if match:
                    json_str = match.group(0)
                else:
                    json_str = content
                
                # Clean up common formatting issues
                json_str = json_str.strip()
                if json_str.startswith('```json'):
                    json_str = json_str[7:]
                if json_str.startswith('```'):
                    json_str = json_str[3:]
                if json_str.endswith('```'):
                    json_str = json_str[:-3]
                json_str = json_str.strip()
                
                # Parse JSON
                job_listings = json.loads(json_str)
                
                # Ensure it's a list
                if not isinstance(job_listings, list):
                    if isinstance(job_listings, dict) and "jobs" in job_listings:
                        job_listings = job_listings["jobs"]
                    else:
                        return []
                
                return job_listings
                
            except Exception as e:
                print(f"Error parsing OpenAI response: {e}")
                return []
                
        except Exception as e:
            print(f"Error in OpenAI extraction: {e}")
            return []
    
    def scrape(self, keywords, location, max_jobs=MAX_JOBS_PER_SOURCE):
        """
        Scrape jobs from the website using OpenAI.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            max_jobs (int): Maximum number of jobs to scrape
            
        Returns:
            pd.DataFrame: DataFrame containing the scraped job listings
        """
        url = self.build_url(keywords, location)
        print(f"Scraping {self.name}...")
        
        try:
            # Request webpage
            response = requests.get(url, headers=self.get_headers())
            html_content = response.text
            
            # Extract jobs
            job_listings = self.extract_jobs_with_openai(html_content)
            
            # Process jobs
            job_count = 0
            
            if not isinstance(job_listings, list):
                return self.jobs_df
            
            for job in job_listings[:max_jobs]:
                try:
                    if not isinstance(job, dict):
                        continue
                    
                    # Extract fields
                    title = str(job.get("title", ""))
                    company = str(job.get("company", ""))
                    job_location = str(job.get("location", location))
                    date = str(job.get("date", "Recent"))
                    link = str(job.get("link", ""))
                    
                    # Process link if needed
                    if link and not link.startswith(("http://", "https://")):
                        base_url = "/".join(url.split("/")[:3])
                        link = f"{base_url}{link if link.startswith('/') else '/' + link}"
                    
                    # Add to dataframe
                    job_data = pd.DataFrame({
                        "title": [title],
                        "company": [company],
                        "location": [job_location],
                        "date": [date],
                        "link": [link],
                        "source": [self.name]
                    })
                    
                    self.jobs_df = pd.concat([self.jobs_df, job_data], ignore_index=True)
                    job_count += 1
                    
                except Exception as e:
                    print(f"Error processing job from {self.name}: {e}")
                    continue
            
            print(f"Found {job_count} jobs from {self.name}")
            
        except Exception as e:
            print(f"Error scraping {self.name}: {e}")
        
        return self.jobs_df