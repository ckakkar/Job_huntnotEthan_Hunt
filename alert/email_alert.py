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
    
    def _format_email_body(self, jobs_df):
        """
        Format the email body with job listings as HTML.
        
        Args:
            jobs_df (pd.DataFrame): DataFrame containing job listings.
        
        Returns:
            str: Formatted email body as HTML.
        """
        # Create HTML header
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; margin-top: 20px; }}
                .job {{ border: 1px solid #e0e0e0; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                .job:hover {{ background-color: #f8f9fa; }}
                .job-title {{ color: #2980b9; font-size: 18px; margin: 0 0 10px 0; }}
                .job-company {{ font-weight: bold; }}
                .job-details {{ color: #7f8c8d; margin: 5px 0; }}
                .job-link {{ display: inline-block; margin-top: 10px; color: white; background-color: #3498db; 
                            padding: 5px 10px; text-decoration: none; border-radius: 3px; }}
                .job-link:hover {{ background-color: #2980b9; }}
                .source-title {{ background-color: #34495e; color: white; padding: 8px; margin-top: 25px; border-radius: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 15px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #95a5a6; }}
                .stats {{ background-color: #f0f3f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>🚀 Job Hunt Results - {datetime.now().strftime("%Y-%m-%d")}</h1>
            
            <div class="stats">
                <p>We found <strong>{len(jobs_df)}</strong> new job postings matching your criteria!</p>
                <p>Keywords: {', '.join(jobs_df['title'].str.extract(r'([A-Za-z]\w+)')[0].dropna().unique().tolist()[:5])}...</p>
            </div>
        """
        
        # Group by source
        grouped = jobs_df.groupby('source')
        
        # Loop through each source
        for source, group in grouped:
            html += f'<h2 class="source-title">{source} ({len(group)} jobs)</h2>'
            
            # Loop through each job in the group
            for i, (_, job) in enumerate(group.iterrows(), 1):
                html += f"""
                <div class="job">
                    <h3 class="job-title">{i}. {job['title']}</h3>
                    <p class="job-company">{job['company']}</p>
                    <p class="job-details">📍 {job['location']}</p>
                    <p class="job-details">⏰ Posted: {job['date']}</p>
                    <a href="{job['link']}" target="_blank" class="job-link">View Job</a>
                </div>
                """
        
        # Add footer
        html += f"""
            <div class="footer">
                <p>Job search completed on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
                <p>This email was automatically generated by JobHunter.</p>
            </div>
        </body>
        </html>
        """
        
        return html