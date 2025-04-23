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
        lambda title: any(keyword in title for keyword in keywords_lower)
    )
    
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
    
    # Check if any location is in the job location
    mask = jobs_df['location'].str.lower().apply(
        lambda loc: any(location in loc for location in locations_lower)
    )
    
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
    
    # Get current time in UTC
    now = datetime.now(pytz.UTC)
    
    # Check for common patterns
    if date_str in ['today', 'just now', 'now', 'few minutes ago']:
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


def filter_recent_jobs(jobs_df, days=1):
    """
    Filter jobs that were posted in the specified number of days.
    
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
        'moments ago', 'just posted', 'new', 'posted today'
    ]
    
    # Compile regex patterns for common time formats
    hour_pattern = re.compile(r'\d+\s*h(ou)?r')
    minute_pattern = re.compile(r'\d+\s*min(ute)?')
    day_pattern = re.compile(r'(\d+)\s*d(ay)?')
    
    # First, try to filter using text patterns
    mask1 = jobs_df['date'].str.lower().apply(
        lambda date: any(indicator in date for indicator in recent_indicators) or
                     hour_pattern.search(date.lower()) is not None or
                     minute_pattern.search(date.lower()) is not None or
                     (day_pattern.search(date.lower()) is not None and 
                      int(day_pattern.search(date.lower()).group(1)) <= days)
    )
    
    # Second, try to parse dates and filter by days ago
    cutoff_date = datetime.now() - timedelta(days=days)
    
    mask2 = jobs_df['date'].apply(
        lambda date_str: 
            parse_date_string(date_str) is not None and 
            parse_date_string(date_str) >= cutoff_date
    )
    
    # Combine both filters with OR
    mask = mask1 | mask2
    
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
    
    # Drop duplicates based on title and company
    return jobs_df.drop_duplicates(subset=['title', 'company']).reset_index(drop=True)


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
        return 0
    
    # Add recency score and sort
    jobs_df['recency_score'] = jobs_df['date'].apply(recency_score)
    sorted_df = jobs_df.sort_values('recency_score', ascending=False).drop('recency_score', axis=1)
    
    return sorted_df.reset_index(drop=True)


def process_jobs(jobs_df, keywords=None, locations=None, recent_days=1, sort_by_date=True):
    """
    Process job listings: filter by keywords, locations, recent only, and remove duplicates.
    
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
    
    # Filter by keywords if provided
    if keywords and len(keywords) > 0:
        processed_df = filter_jobs_by_keywords(processed_df, keywords)
    
    # Filter by locations if provided
    if locations and len(locations) > 0:
        processed_df = filter_jobs_by_location(processed_df, locations)
    
    # Filter for recent jobs
    processed_df = filter_recent_jobs(processed_df, days=recent_days)
    
    # Remove duplicates
    processed_df = remove_duplicates(processed_df)
    
    # Sort by date if requested
    if sort_by_date:
        processed_df = sort_jobs_by_date(processed_df)
    
    return processed_df