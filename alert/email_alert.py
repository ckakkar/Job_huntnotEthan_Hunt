"""Email alert system for job notifications."""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime

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
        if not link or len(link) < 10 or not (link.startswith('http://') or link.startswith('https://')):
            # Generate a generic search link as fallback
            return "https://www.google.com/search?q=jobs+in+bangalore"
        return link
    
    def _format_email_body(self, jobs_df):
        """
        Format the email body with job listings as HTML.
        
        Args:
            jobs_df (pd.DataFrame): DataFrame containing job listings.
        
        Returns:
            str: Formatted email body as HTML.
        """
        # Create extremely simple HTML without complex CSS
        html = f"""
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Hi PUU - {datetime.now().strftime("%Y-%m-%d")}</h1>
            
            <div style="background-color: #f0f0f0; padding: 10px; margin: 10px 0;">
                <p>Found <strong>{len(jobs_df)}</strong> new job postings matching your criteria!</p>
                <p>Looking for jobs posted in the last 7 days</p>
            </div>
        """
        
        # Group by source
        grouped = jobs_df.groupby('source')
        
        # Loop through each source
        for source, group in grouped:
            html += f'<h2 style="color: #3366cc;">{source} ({len(group)} jobs)</h2>'
            
            # Loop through each job in the group
            for i, (_, job) in enumerate(group.iterrows(), 1):
                # Ensure link is valid
                link = self._validate_link(job['link'])
                
                html += f"""
                <div style="border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;">
                    <h3>{i}. {job['title']}</h3>
                    <p><strong>{job['company']}</strong></p>
                    <p>📍 {job['location']}</p>
                    <p>⏰ Posted: {job['date']}</p>
                    <a href="{link}" target="_blank" style="background-color: #3366cc; color: white; padding: 5px 10px; text-decoration: none;">View Job</a>
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