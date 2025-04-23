"""GitHub Jobs API for tech job postings."""
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus

from config.config import USER_AGENT, MAX_JOBS_PER_SOURCE

class GitHubJobsAPI:
    """
    GitHub Jobs API for tech positions.
    This is particularly useful for software engineering roles.
    """
    
    def __init__(self):
        """Initialize the GitHub Jobs API client."""
        self.name = "GitHub Jobs"
        self.api_url = "https://jobs.github.com/positions.json"
        self.jobs_df = pd.DataFrame(columns=["title", "company", "location", "date", "link", "source"])
    
    def get_headers(self):
        """Return the headers to use for requests."""
        return {
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        }
    
    def search(self, keywords, location, days=1, max_jobs=MAX_JOBS_PER_SOURCE):
        """
        Search for jobs on GitHub Jobs.
        
        Args:
            keywords (str): Keywords to search for
            location (str): Location to search in
            days (int): Number of days to look back (filter applied after fetching)
            max_jobs (int): Maximum number of jobs to return
            
        Returns:
            pd.DataFrame: DataFrame containing job listings
        """
        url = self.api_url
        params = {
            "description": keywords,
            "location": location
        }
        
        print(f"Searching GitHub Jobs for {keywords} in {location}")
        
        try:
            response = requests.get(url, params=params, headers=self.get_headers())
            
            if response.status_code != 200:
                print(f"Failed to get response from GitHub Jobs: {response.status_code}")
                return self.jobs_df
            
            jobs = response.json()
            
            if not jobs:
                print("No jobs found on GitHub Jobs")
                return self.jobs_df
            
            # Filter for jobs posted in the last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in jobs[:max_jobs]:
                try:
                    # Parse the date string
                    date_str = job.get("created_at")
                    job_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S UTC %Y")
                    
                    # Skip jobs older than the cutoff
                    if job_date < cutoff_date:
                        continue
                    
                    self.jobs_df = pd.concat([
                        self.jobs_df,
                        pd.DataFrame({
                            "title": [job.get("title", "")],
                            "company": [job.get("company", "")],
                            "location": [job.get("location", "")],
                            "date": [date_str],
                            "link": [job.get("url", "")],
                            "source": [self.name]
                        })
                    ], ignore_index=True)
                except Exception as e:
                    print(f"Error processing GitHub job: {e}")
                    continue
            
            print(f"Found {len(self.jobs_df)} recent jobs from GitHub Jobs")
            
        except Exception as e:
            print(f"Error searching GitHub Jobs: {e}")
        
        return self.jobs_df
    
    def is_available(self):
        """
        Check if the GitHub Jobs API is still available.
        (GitHub Jobs was deprecated but is included here for completeness)
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        try:
            response = requests.get(self.api_url, headers=self.get_headers())
            # Even if the API returns a 404, it might redirect to a new URL
            return response.status_code == 200
        except:
            return False