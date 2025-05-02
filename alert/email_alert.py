"""Email alert system for job notifications."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime
import re
import urllib.parse

from config.credentials import EMAIL


class EmailAlert:
    """Email alert system for job notifications."""
    
    def __init__(self):
        """Initialize the email alert system."""
        self.sender = EMAIL["sender"]
        self.password = EMAIL["password"]
        self.recipient = EMAIL["recipient"]
        self.smtp_server = EMAIL["smtp_server"]
        self.smtp_port = EMAIL["smtp_port"]
    
    def is_enabled(self):
        """Check if email alerts are enabled."""
        return all([
            self.sender, self.password, self.recipient, self.smtp_server, self.smtp_port
        ])
    
    def send_alert(self, jobs_df):
        """
        Send an email alert with the job listings.
        
        Args:
            jobs_df (pd.DataFrame): DataFrame containing job listings.
        
        Returns:
            bool: True if the email was sent successfully, False otherwise.
        """
        if not self.is_enabled():
            print("Email alerts are not configured properly. Check your .env file.")
            return False
        
        if jobs_df.empty:
            print("No jobs to send email alert for.")
            return False
        
        try:
            # Create email content
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"🚨 {len(jobs_df)} New Jobs Found in Bangalore – {today}"
            body = self._format_email_body(jobs_df)
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.sender
            msg["To"] = self.recipient
            msg["Subject"] = subject
            
            # Attach body
            msg.attach(MIMEText(body, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            print(f"Email alert sent with {len(jobs_df)} job listings.")
            return True
            
        except Exception as e:
            print(f"Error sending email alert: {e}")
            return False
    
    def _validate_link(self, link):
        """
        Ensure the link is valid and properly formatted.
        
        Args:
            link (str): The link to validate
            
        Returns:
            str: Valid link or search fallback
        """
        # Make sure the link is a string
        link = str(link).strip()
        
        # Check if link is empty or too short
        if not link or len(link) < 5:
            return self._generate_search_link("jobs in bangalore")
        
        # Fix common issues with links
        if not link.startswith(('http://', 'https://')):
            if link.startswith('www.'):
                link = 'https://' + link
            else:
                # Try to extract a domain if present
                domain_match = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z0-9][-a-zA-Z0-9]*', link)
                if domain_match:
                    domain = domain_match.group(0)
                    link = 'https://' + domain
                else:
                    # No valid domain found
                    return self._generate_search_link(link)
        
        # Check for common placeholder links that need to be avoided
        invalid_domains = ['example.com', 'example.org', 'test.com', 'localhost']
        if any(invalid in link.lower() for invalid in invalid_domains):
            return self._generate_search_link("job openings in bangalore")
        
        return link
    
    def _generate_search_link(self, query):
        """Generate a Google search link with the provided query."""
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.google.com/search?q={encoded_query}"
    
    def _format_email_body(self, jobs_df):
        """
        Format the email body with job listings as HTML.
        
        Args:
            jobs_df (pd.DataFrame): DataFrame containing job listings.
        
        Returns:
            str: Formatted email body as HTML.
        """
        # Create HTML with proper styling
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .job-card {{ border: 1px solid #ccc; padding: 15px; margin-bottom: 15px; border-radius: 8px; background-color: #f9f9f9; }}
                .job-title {{ color: #2c5282; margin-top: 0; margin-bottom: 10px; font-size: 18px; }}
                .job-company {{ font-weight: bold; margin: 5px 0; color: #444; }}
                .job-details {{ color: #555; margin: 5px 0; }}
                .job-link {{ 
                    display: inline-block;
                    background-color: #3366cc; 
                    color: white !important; 
                    padding: 8px 15px; 
                    text-decoration: none !important; 
                    border-radius: 4px; 
                    margin-top: 10px;
                    font-weight: bold;
                }}
                .header {{ background-color: #f0f0f0; padding: 15px; margin: 10px 0; border-radius: 8px; }}
                .section-heading {{ color: #3366cc; margin-top: 25px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                .debug-info {{ font-size: 10px; color: #999; margin-top: 3px; }}
            </style>
        </head>
        <body>
            <h1>Hi PUU - {datetime.now().strftime("%Y-%m-%d")}</h1>
            
            <div class="header">
                <p>Found <strong>{len(jobs_df)}</strong> new job postings matching your criteria!</p>
                <p>Looking for jobs posted in the last 7 days</p>
            </div>
        """
        
        # Group by source
        grouped = jobs_df.groupby('source')
        
        # Loop through each source
        for source, group in grouped:
            html += f'<h2 class="section-heading">{source} ({len(group)} jobs)</h2>'
            
            # Loop through each job in the group
            for i, (_, job) in enumerate(group.iterrows(), 1):
                # Get original link for debugging
                original_link = job['link'] if 'link' in job else "No link provided"
                
                # Ensure link is valid
                link = self._validate_link(original_link)
                
                html += f"""
                <div class="job-card">
                    <h3 class="job-title">{i}. {job['title']}</h3>
                    <p class="job-company">{job['company']}</p>
                    <p class="job-details">📍 {job['location']}</p>
                    <p class="job-details">⏰ Posted: {job['date']}</p>
                    <a href="{link}" target="_blank" class="job-link">View Job</a>
                </div>
                """
        
        # Add footer
        html += f"""
            <div style="margin-top: 20px; padding-top: 10px; border-top: 1px solid #ccc;">
                <p>Job search completed on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
                <p>This email was automatically generated by JobHunter.</p>
            </div>
        </body>
        </html>
        """
        
        return html