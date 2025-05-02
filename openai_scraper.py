"""Enhanced OpenAI-powered job scraper optimized for cost-efficiency and reliability."""
import requests
import json
import time
import os
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class OpenAIScraper:
    """
    An enhanced job scraper that uses OpenAI to extract structured job data from HTML.
    Improved with better prompts and error handling.
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
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
    
    def build_url(self, keywords, location):
        """Build the URL for the job search."""
        encoded_keywords = quote_plus(keywords)
        encoded_location = quote_plus(location)
        try:
            return self.url_template.format(keywords=encoded_keywords, location=encoded_location)
        except KeyError:
            # Some templates might not have both placeholders
            if "{keywords}" in self.url_template and "{location}" not in self.url_template:
                return self.url_template.format(keywords=encoded_keywords)
            elif "{location}" in self.url_template and "{keywords}" not in self.url_template:
                return self.url_template.format(location=encoded_location)
            return self.url_template  # Use as-is if no placeholders
    
    def preprocess_html(self, html_content):
        """
        Preprocess HTML to extract the most relevant parts for job listings.
        
        Args:
            html_content (str): Raw HTML content
            
        Returns:
            str: Preprocessed text focused on job listings
        """
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Remove script and style tags
        for script in soup(["script", "style", "svg", "path", "meta", "link"]):
            script.extract()
        
        # Try to focus on main content area
        main_content = None
        
        # Site-specific targeting
        if "linkedin.com" in self.url_template:
            main_content = soup.select_one(".jobs-search__results-list, .jobs-search-results-list")
        elif "indeed.com" in self.url_template:
            main_content = soup.select_one("#mosaic-provider-jobcards, .jobsearch-ResultsList")
        elif "naukri.com" in self.url_template:
            main_content = soup.select_one(".list")
        elif "foundit.in" in self.url_template or "monster.com" in self.url_template:
            main_content = soup.select_one("#srp-jobList")
        elif "jpmorgan" in self.url_template:
            main_content = soup.select_one(".jobs-list")
        elif "goldmansachs" in self.url_template:
            main_content = soup.select_one(".job-tile-container")
        elif "efinancialcareers" in self.url_template:
            main_content = soup.select_one(".jobs-list")
            
        # Try generic selectors if no site-specific content found
        if not main_content:
            for selector in [
                "main", "#main", ".main", "#content", ".content", "#jobs", ".jobs",
                "#job-search-results", ".job-search-results", ".job-list", ".jobslist",
                "article", "section", ".listing", "#listing", ".search-results", "#search-results"
            ]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
        
        # If main content area is found, use it
        if main_content:
            text_blocks = []
            
            # Extract all job cards in the main content
            job_cards = main_content.select(
                ".job-card, .job-listing, .job-result, div[class*='job'], li[class*='job'], "
                ".search-result, .result, article, [data-job-id], [data-jobid], "
                "[class*='card'], [class*='listing']"
            )
            
            if job_cards:
                # Process each job card
                for card in job_cards[:25]:  # Process up to 25 job cards to limit tokens
                    # Extract text from card with basic structure
                    card_text = ""
                    
                    # Title
                    title_elem = card.select_one("h1, h2, h3, h4, .title, [class*='title']")
                    if title_elem:
                        card_text += f"Title: {title_elem.text.strip()}\n"
                    
                    # Company
                    company_elem = card.select_one(".company, [class*='company'], .employer, [class*='employer']")
                    if company_elem:
                        card_text += f"Company: {company_elem.text.strip()}\n"
                    
                    # Location
                    location_elem = card.select_one(".location, [class*='location'], .loc, [class*='loc']")
                    if location_elem:
                        card_text += f"Location: {location_elem.text.strip()}\n"
                    
                    # Date
                    date_elem = card.select_one(".date, [class*='date'], time, .posted")
                    if date_elem:
                        card_text += f"Date: {date_elem.text.strip()}\n"
                    
                    # If we couldn't extract structured data, use the whole card text
                    if not card_text:
                        card_text = card.get_text(separator=" ", strip=True)
                    
                    text_blocks.append(card_text)
                
                # Join all job card texts
                focused_text = "\n---\n".join(text_blocks)
            else:
                # If no job cards found but we have main content, use the full text
                focused_text = main_content.get_text(separator=" ", strip=True)
        else:
            # If no main content identified, use a subset of the body
            body = soup.body
            if body:
                # Try to remove headers, footers, navigation
                for selector in ["header", "footer", "nav", ".nav", "#nav", ".header", "#header", ".footer", "#footer"]:
                    for element in body.select(selector):
                        element.extract()
                
                # Get the resulting text
                focused_text = body.get_text(separator=" ", strip=True)
            else:
                # Fallback to the whole document
                focused_text = soup.get_text(separator=" ", strip=True)
        
        # Limit text length for token efficiency
        max_chars = 10000
        if len(focused_text) > max_chars:
            focused_text = focused_text[:max_chars]
        
        return focused_text
    
    def extract_jobs_with_openai(self, html_content, keywords, location):
        """
        Extract job listings from HTML content using OpenAI.
        
        Args:
            html_content (str): HTML content of the job listings page
            keywords (str): Job keywords being searched
            location (str): Location being searched
            
        Returns:
            list: List of dictionaries containing job details
        """
        if not self.api_key:
            print(f"OpenAI API key required for {self.name} scraper")
            return []
        
        try:
            # Preprocess HTML to extract the most relevant parts
            processed_text = self.preprocess_html(html_content)
            
            # Skip if processed text is too short
            if len(processed_text) < 100:
                print(f"Warning: Processed text from {self.name} is too short")
                return []
            
            # Create specific system message for different sites
            system_message = "Extract job listings from web pages as structured JSON only."
            
            if "jpmorgan" in self.url_template.lower() or "goldman" in self.url_template.lower():
                system_message += " This is a major bank's career page with finance and banking jobs."
            elif "efinancial" in self.url_template.lower():
                system_message += " This is a specialized finance job site."
            
            # Create a specialized prompt based on the source
            source_info = ""
            if "linkedin.com" in self.url_template:
                source_info = "This is a LinkedIn jobs page. Look for job-card elements with titles, companies, and locations."
            elif "indeed.com" in self.url_template:
                source_info = "This is an Indeed jobs page. Look for job listings with titles, companies, and locations."
            elif "naukri.com" in self.url_template:
                source_info = "This is a Naukri jobs page. Look for job tuples with titles, companies, and locations."
            
            prompt = f"""
            Extract job listings from this job search webpage as a JSON array of job objects.
            
            {source_info}
            
            Looking for jobs matching: {keywords}
            Location: {location}
            
            Each job object should have:
            - title: The job title (REQUIRED)
            - company: The company name (REQUIRED)
            - location: The job location (REQUIRED - with focus on Bangalore/Bengaluru jobs)
            - date: When the job was posted (if available)
            - link: The URL to the job listing (if available)
            
            IMPORTANT:
            1. ONLY extract jobs that appear to be actual job listings.
            2. Focus on finance, banking, investment, regulatory, compliance, and operations roles.
            3. Extract ALL jobs you can find, even if some fields are missing.
            4. If location is missing, use "Bangalore" as default.
            5. If you're not 100% sure about a field, still include your best guess.
            
            Format as a valid JSON array. For example:
            [
              {{
                "title": "Financial Analyst",
                "company": "Example Bank",
                "location": "Bangalore",
                "date": "Posted 2 days ago",
                "link": "https://example.com/jobs/123"
              }},
              ...
            ]
            
            Webpage text content:
            {processed_text}
            """
            
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
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2500,
                    "response_format": {"type": "json_object"}
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Error from OpenAI API: {response.status_code} - {response.text}")
                return []
            
            # Parse response
            result = response.json()
            
            # Extract content
            if "choices" not in result or not result["choices"]:
                return []
                
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON
            try:
                # Parse the returned JSON
                parsed_content = json.loads(content)
                
                # Look for a jobs array
                if "jobs" in parsed_content:
                    return parsed_content["jobs"]
                
                # If the response is a list, use it directly
                if isinstance(parsed_content, list):
                    return parsed_content
                
                # If we have a nested structure, try to find job listings
                for key, value in parsed_content.items():
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        if "title" in value[0] or "company" in value[0]:
                            return value
                
                # If we couldn't find a list, try to extract any job-like objects
                job_listings = []
                for key, value in parsed_content.items():
                    if isinstance(value, dict) and ("title" in value or "company" in value):
                        job_listings.append(value)
                
                if job_listings:
                    return job_listings
                
                # If all else fails, return an empty list
                return []
                
            except Exception as e:
                print(f"Error parsing OpenAI response: {e}")
                # Try to extract JSON with regex as a last resort
                import re
                json_pattern = re.compile(r'\[\s*\{.*\}\s*\]', re.DOTALL)
                match = json_pattern.search(content)
                
                if match:
                    try:
                        json_str = match.group(0)
                        return json.loads(json_str)
                    except:
                        return []
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
        print(f"Scraping {self.name} using OpenAI...")
        
        try:
            # Request webpage with timeout and retry
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=self.get_headers(), timeout=20)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 403:
                        print(f"Access denied (403) when accessing {self.name}. Using a different User-Agent...")
                        headers = self.get_headers()
                        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                    else:
                        print(f"Attempt {attempt+1}: Error {response.status_code} when accessing {self.name}")
                    time.sleep(2)
                except requests.exceptions.RequestException as e:
                    print(f"Attempt {attempt+1}: Request error for {self.name}: {e}")
                    time.sleep(2)
            
            if response.status_code != 200:
                print(f"Failed to access {self.name} after {max_retries} attempts")
                return self.jobs_df
            
            html_content = response.text
            
            # Skip if the page contains no useful content
            if len(html_content) < 1000 or "no jobs found" in html_content.lower():
                print(f"No useful content found on {self.name}")
                return self.jobs_df
            
            # Extract jobs using OpenAI
            job_listings = self.extract_jobs_with_openai(html_content, keywords, location)
            
            # Process jobs
            job_count = 0
            
            if not isinstance(job_listings, list):
                print(f"No valid job listings found on {self.name}")
                return self.jobs_df
            
            for job in job_listings[:max_jobs]:
                try:
                    if not isinstance(job, dict):
                        continue
                    
                    # Extract fields
                    title = str(job.get("title", "")).strip()
                    company = str(job.get("company", "")).strip()
                    job_location = str(job.get("location", location)).strip()
                    date = str(job.get("date", "Within 7 days")).strip()
                    link = str(job.get("link", "")).strip()
                    
                    # Skip entries without title or company
                    if not title or not company:
                        continue
                    
                    # Clean up location - default to Bangalore if unclear
                    if not job_location or len(job_location) < 3:
                        job_location = "Bangalore"
                    
                    # Process link if needed
                    if link and not link.startswith(("http://", "https://")):
                        base_url = "/".join(url.split("/")[:3])
                        link = f"{base_url}{link if link.startswith('/') else '/' + link}"
                    
                    # Default date if missing
                    if not date or date.lower() in ["none", "n/a", "null", ""]:
                        date = "Recently posted"
                    
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