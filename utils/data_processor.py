"""Data processing utilities for job listings."""
import pandas as pd
import re
from datetime import datetime, timedelta
import pytz


def filter_jobs_by_keywords(jobs_df, keywords):
    """
    Filter jobs by keywords in job title.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
        keywords (list): List of keywords to filter by.
    
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Convert keywords to lowercase for case-insensitive matching
    keywords_lower = [k.lower() for k in keywords]
    
    # Check if any keyword is in the job title
    mask = jobs_df['title'].str.lower().apply(
        lambda title: any(keyword in title.lower() for keyword in keywords_lower)
    )
    
    # If filtering removes all jobs, return the original DataFrame
    if not mask.any():
        print("Warning: Keyword filtering removed all jobs. Returning all jobs.")
        return jobs_df
    
    return jobs_df[mask].reset_index(drop=True)


def filter_jobs_by_title_keywords(jobs_df, title_keywords):
    """
    Filter jobs by keywords in the job title.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
        title_keywords (list): List of keywords to filter by in the title.
    
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Convert keywords to lowercase for case-insensitive matching
    keywords_lower = [k.lower() for k in title_keywords]
    
    # Check if any keyword is in the job title
    mask = jobs_df['title'].str.lower().apply(
        lambda title: any(keyword in title.lower() for keyword in keywords_lower)
    )
    
    # If we have too few matches (less than 10 or less than 25% of original), return original
    if mask.sum() < 10 or mask.sum() < len(jobs_df) * 0.25:
        print(f"Warning: Title keyword filtering kept only {mask.sum()} of {len(jobs_df)} jobs. Returning all jobs.")
        return jobs_df
    
    return jobs_df[mask].reset_index(drop=True)


def filter_jobs_by_location(jobs_df, locations):
    """
    Filter jobs by location.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
        locations (list): List of locations to filter by.
    
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Convert locations to lowercase for case-insensitive matching
    locations_lower = [l.lower() for l in locations]
    
    # Add remote/hybrid to locations if not already included
    if not any('remote' in loc for loc in locations_lower):
        locations_lower.append('remote')
    if not any('hybrid' in loc for loc in locations_lower):
        locations_lower.append('hybrid')
    
    # Check if any location is in the job location
    mask = jobs_df['location'].str.lower().apply(
        lambda loc: any(location in loc.lower() for location in locations_lower)
    )
    
    # If filtering removes too many jobs, be more lenient
    if mask.sum() < 10 and len(jobs_df) > 10:
        print("Warning: Strict location filtering removed too many jobs. Using more lenient filtering.")
        # More lenient approach - just check for Bangalore/Bengaluru or Remote
        mask = jobs_df['location'].str.lower().apply(
            lambda loc: 'bangalore' in loc.lower() or 'bengaluru' in loc.lower() or 
                        'remote' in loc.lower() or 'hybrid' in loc.lower() or 
                        'anywhere' in loc.lower() or 'india' in loc.lower()
        )
    
    # If still too strict, return all jobs
    if mask.sum() < 5 and len(jobs_df) > 10:
        print("Warning: Location filtering removed too many jobs. Returning all jobs.")
        return jobs_df
    
    return jobs_df[mask].reset_index(drop=True)


def parse_date_string(date_str):
    """
    Parse various date string formats into a datetime object.
    
    Args:
        date_str (str): Date string to parse
        
    Returns:
        datetime or None: Parsed datetime object or None if parsing fails
    """
    # Convert to string if not already
    date_str = str(date_str).lower().strip()
    
    # Get current time (without timezone info)
    now = datetime.now()
    
    # Check for common patterns
    if date_str in ['today', 'just now', 'now', 'few minutes ago', 'recently posted']:
        return now
    
    if 'minute' in date_str or 'minutes' in date_str:
        minutes = re.search(r'(\d+)', date_str)
        if minutes:
            return now - timedelta(minutes=int(minutes.group(1)))
        return now
    
    if 'hour' in date_str or 'hours' in date_str:
        hours = re.search(r'(\d+)', date_str)
        if hours:
            return now - timedelta(hours=int(hours.group(1)))
        return now
    
    if date_str in ['yesterday', '1 day ago']:
        return now - timedelta(days=1)
    
    if 'day' in date_str or 'days' in date_str:
        days = re.search(r'(\d+)', date_str)
        if days:
            return now - timedelta(days=int(days.group(1)))
    
    if 'week' in date_str or 'weeks' in date_str:
        weeks = re.search(r'(\d+)', date_str)
        if weeks:
            return now - timedelta(weeks=int(weeks.group(1)))
    
    if date_str in ['within last 7 days', 'past week', 'recent', 'posted recently']:
        return now - timedelta(days=3)  # Assume middle of the week
    
    if 'month' in date_str or 'months' in date_str:
        months = re.search(r'(\d+)', date_str)
        if months:
            # Approximate month as 30 days
            return now - timedelta(days=int(months.group(1)) * 30)
    
    # Try common date formats
    formats = [
        '%Y-%m-%d',  # 2023-04-22
        '%d/%m/%Y',  # 22/04/2023
        '%m/%d/%Y',  # 04/22/2023
        '%b %d, %Y',  # Apr 22, 2023
        '%B %d, %Y',  # April 22, 2023
        '%d %b %Y',   # 22 Apr 2023
        '%d %B %Y',   # 22 April 2023
        '%Y/%m/%d',   # 2023/04/22
        '%a %b %d %H:%M:%S UTC %Y'  # GitHub API format
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def filter_recent_jobs(jobs_df, days=7):
    """
    Filter jobs that were posted in the specified number of days.
    More lenient to avoid filtering out too many jobs.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
        days (int): Number of days to look back
    
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # List of strings that indicate recent jobs
    recent_indicators = [
        'today', 'just now', 'few hours ago', 'hour ago',
        'hours ago', 'yesterday', '1 day ago', 'recent',
        'moments ago', 'just posted', 'new', 'posted today',
        'within last 7 days', 'recently posted', 'past week',
        'few days ago', 'this week'
    ]
    
    # Compile regex patterns for common time formats
    hour_pattern = re.compile(r'\d+\s*h(ou)?r')
    minute_pattern = re.compile(r'\d+\s*min(ute)?')
    day_pattern = re.compile(r'(\d+)\s*d(ay)?')
    week_pattern = re.compile(r'(\d+)\s*week')
    
    # First, try to filter using text patterns
    mask1 = jobs_df['date'].str.lower().apply(
        lambda date: any(indicator in date.lower() for indicator in recent_indicators) or
                     hour_pattern.search(date.lower()) is not None or
                     minute_pattern.search(date.lower()) is not None or
                     (day_pattern.search(date.lower()) is not None and 
                      int(day_pattern.search(date.lower()).group(1)) <= max(days, 30)) or
                     (week_pattern.search(date.lower()) is not None and
                      int(week_pattern.search(date.lower()).group(1)) <= max(days // 7, 4))
    )
    
    # If filtering is too strict, be more lenient with days
    if mask1.sum() < len(jobs_df) * 0.3 and days <= 7:
        # For 7-day searches, allow up to 30 days
        extended_days = 30
        mask1 = jobs_df['date'].str.lower().apply(
            lambda date: any(indicator in date.lower() for indicator in recent_indicators) or
                        hour_pattern.search(date.lower()) is not None or
                        minute_pattern.search(date.lower()) is not None or
                        (day_pattern.search(date.lower()) is not None and 
                        int(day_pattern.search(date.lower()).group(1)) <= extended_days) or
                        (week_pattern.search(date.lower()) is not None and
                        int(week_pattern.search(date.lower()).group(1)) <= (extended_days // 7))
        )
    
    # Second, try to parse dates and filter by days ago
    cutoff_date = datetime.now() - timedelta(days=max(days, 30))  # Be lenient with date filtering
    
    # Use a function that safely checks if a date is recent without timezone issues
    def is_recent_date(date_str):
        parsed_date = parse_date_string(date_str)
        if parsed_date is None:
            return True  # If we can't parse, assume it's recent
        
        # Now ensure we're comparing naive datetimes
        return parsed_date >= cutoff_date
    
    mask2 = jobs_df['date'].apply(is_recent_date)
    
    # Combine both filters with OR
    mask = mask1 | mask2
    
    # As a fallback, if we've filtered out too many jobs, return all jobs
    if mask.sum() < 10 and len(jobs_df) > 15:
        print(f"Warning: Date filtering kept only {mask.sum()} of {len(jobs_df)} jobs. Returning all jobs.")
        return jobs_df
    
    return jobs_df[mask].reset_index(drop=True)


def remove_duplicates(jobs_df):
    """
    Remove duplicate job listings based on title and company.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
    
    Returns:
        pd.DataFrame: DataFrame with duplicates removed.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Clean titles and companies for better matching
    jobs_df['clean_title'] = jobs_df['title'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', '', x))
    jobs_df['clean_company'] = jobs_df['company'].str.lower().apply(lambda x: re.sub(r'[^\w\s]', '', x))
    
    # Drop duplicates based on clean title and company
    deduplicated_df = jobs_df.drop_duplicates(subset=['clean_title', 'clean_company']).reset_index(drop=True)
    
    # Remove the temporary columns
    deduplicated_df = deduplicated_df.drop(['clean_title', 'clean_company'], axis=1)
    
    return deduplicated_df


def sort_jobs_by_date(jobs_df):
    """
    Sort jobs by date (most recent first).
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
    
    Returns:
        pd.DataFrame: Sorted DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Function to calculate recency score (higher for more recent)
    def recency_score(date_str):
        # Recent indicators have high scores
        if any(indicator in date_str.lower() for indicator in ['just now', 'few minutes', 'moments ago']):
            return 1000
        if 'hour' in date_str.lower():
            match = re.search(r'(\d+)', date_str)
            if match:
                hours = int(match.group(1))
                return 900 - hours
            return 800
        if 'today' in date_str.lower():
            return 700
        if 'yesterday' in date_str.lower() or '1 day' in date_str.lower():
            return 600
        if 'day' in date_str.lower():
            match = re.search(r'(\d+)', date_str)
            if match:
                days = int(match.group(1))
                return 500 - days
            return 400
        if 'week' in date_str.lower() or 'within last 7 days' in date_str.lower():
            return 300
        return 0
    
    # Add recency score and sort
    jobs_df['recency_score'] = jobs_df['date'].apply(recency_score)
    sorted_df = jobs_df.sort_values('recency_score', ascending=False).drop('recency_score', axis=1)
    
    return sorted_df.reset_index(drop=True)


def enrich_job_data(jobs_df):
    """
    Enrich job listings with additional information.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
    
    Returns:
        pd.DataFrame: Enriched DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Make sure all links are valid
    jobs_df['link'] = jobs_df['link'].apply(
        lambda link: link if link and (link.startswith('http://') or link.startswith('https://')) 
                   else ""
    )
    
    # Fix any empty links by generating fallback links
    def generate_fallback_link(row):
        if not row['link'] or len(row['link']) < 10:
            company = row['company'].replace(' ', '+')
            title = row['title'].replace(' ', '+')
            location = row['location'].replace(' ', '+')
            source = row['source']
            
            if source == 'Indeed':
                return f"https://in.indeed.com/jobs?q={title}+{company}&l={location}"
            elif source == 'Naukri':
                return f"https://www.naukri.com/jobs-in-{location}?keywordsearch={title}"
            elif source == 'LinkedIn':
                return f"https://www.linkedin.com/jobs/search/?keywords={title}&location={location}"
            elif source == 'Foundit':
                return f"https://www.foundit.in/srp/results?keyword={title}&location={location}"
            else:
                return f"https://www.google.com/search?q={title}+{company}+jobs+in+{location}"
        else:
            return row['link']
            
    jobs_df['link'] = jobs_df.apply(generate_fallback_link, axis=1)
    
    # Clean up company names
    jobs_df['company'] = jobs_df['company'].apply(
        lambda company: re.sub(r'\(.*?\)', '', company).strip()  # Remove parenthesis content
    )
    
    # Clean up location names
    jobs_df['location'] = jobs_df['location'].apply(
        lambda location: location.replace(',', ', ').strip()  # Add space after commas
    )
    
    return jobs_df


def process_jobs(jobs_df, keywords=None, locations=None, recent_days=7, sort_by_date=True):
    """
    Process job listings: filter by keywords, locations, recent only, and remove duplicates.
    Less aggressive filtering to ensure we don't lose too many results.
    
    Args:
        jobs_df (pd.DataFrame): DataFrame containing job listings.
        keywords (list): List of keywords to filter by.
        locations (list): List of locations to filter by.
        recent_days (int): Number of days to look back for recent jobs.
        sort_by_date (bool): Whether to sort jobs by date.
    
    Returns:
        pd.DataFrame: Processed DataFrame.
    """
    if jobs_df.empty:
        return jobs_df
    
    # Make a copy to avoid modifying the original
    processed_df = jobs_df.copy()
    
    # Fill missing values
    processed_df['location'] = processed_df['location'].fillna('Bangalore')
    processed_df['date'] = processed_df['date'].fillna('Recent')
    processed_df['company'] = processed_df['company'].fillna('Unknown')
    
    # Remove any rows with empty titles
    processed_df = processed_df[processed_df['title'].notna() & (processed_df['title'] != '')].reset_index(drop=True)
    
    # Enrich job data
    processed_df = enrich_job_data(processed_df)
    
    # Remove duplicates
    processed_df = remove_duplicates(processed_df)
    
    # Filter by keywords if provided - but only if we have enough jobs
    if keywords and len(keywords) > 0 and len(processed_df) >= 20:
        keyword_filtered = filter_jobs_by_keywords(processed_df, keywords)
        # Only apply the filter if it doesn't remove too many jobs
        if len(keyword_filtered) >= max(10, len(processed_df) * 0.3):
            processed_df = keyword_filtered
    
    # Filter by locations if provided - but only if we have enough jobs
    if locations and len(locations) > 0 and len(processed_df) >= 15:
        location_filtered = filter_jobs_by_location(processed_df, locations)
        # Only apply the filter if it doesn't remove too many jobs
        if len(location_filtered) >= max(10, len(processed_df) * 0.3):
            processed_df = location_filtered
    
    # Filter for recent jobs - using extended timeframe
    processed_df = filter_recent_jobs(processed_df, days=recent_days)
    
    # Sort by date if requested
    if sort_by_date:
        processed_df = sort_jobs_by_date(processed_df)
    
    return processed_df