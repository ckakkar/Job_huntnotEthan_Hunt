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
            subject = f"🔥 {len(jobs_df)} Finance Jobs Found in Bangalore – {today}"
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
        Ensure the link is valid and properly formatted - now more permissive.
        
        Args:
            link (str): The link to validate
            
        Returns:
            str: Valid link, original link, or search fallback as a last resort
        """
        # Make sure the link is a string
        link = str(link).strip()
        
        # Check if link is empty or too short - only then use search fallback
        if not link or len(link) < 5:
            return self._generate_search_link("jobs in bangalore")
        
        # Fix common issues with links but preserve the original path
        if not link.startswith(('http://', 'https://')):
            if link.startswith('www.'):
                # Add https:// to www. links
                return 'https://' + link
            else:
                # Try to extract a domain if present
                domain_match = re.search(r'([a-zA-Z0-9][-a-zA-Z0-9]*\.)+[a-zA-Z0-9][-a-zA-Z0-9]*', link)
                if domain_match:
                    domain = domain_match.group(0)
                    # Preserve everything after the domain
                    domain_start = link.find(domain)
                    if domain_start >= 0:
                        path = link[domain_start + len(domain):]
                        return 'https://' + domain + path
                    else:
                        return 'https://' + domain
                else:
                    # Only use search as a last resort when no domain is found
                    return self._generate_search_link(link)
        
        # Check for common placeholder links that need to be avoided
        invalid_domains = ['example.com', 'example.org', 'test.com', 'localhost']
        if any(invalid in link.lower() for invalid in invalid_domains):
            # For invalid examples, we'll still use search
            return self._generate_search_link("job openings in bangalore")
        
        # Return the original link in most cases
        return link
    
    def _generate_search_link(self, query):
        """
        Generate a more specific job search query with company name when possible.
        
        Args:
            query (str): Base query to enhance
            
        Returns:
            str: Enhanced search link
        """
        # Make the query more specific to job listings
        if 'job' not in query.lower():
            query = query + " job openings in bangalore"
        
        encoded_query = urllib.parse.quote_plus(query)
        # Use Indeed or LinkedIn instead of generic Google search when possible
        if any(keyword in query.lower() for keyword in ['finance', 'bank', 'invest', 'analyst']):
            return f"https://in.indeed.com/jobs?q={encoded_query}"
        else:
            return f"https://www.linkedin.com/jobs/search/?keywords={encoded_query}"
    
    def _format_email_body(self, jobs_df):
        """
        Format the email body with job listings as HTML - now with modern design.
        
        Args:
            jobs_df (pd.DataFrame): DataFrame containing job listings.
        
        Returns:
            str: Formatted email body as HTML.
        """
        # Generate colors based on sources for visual distinction
        source_colors = {
            "Indeed": "#2164f3",
            "LinkedIn": "#0077b5",
            "Naukri": "#4a90e2",
            "Foundit": "#ff6000",
            "TimesJobs": "#3c1053",
            "Shine": "#f7941d",
            "GitHub Jobs": "#333333",
            "eFinancialCareers": "#0d3c55",
            "JPMorgan": "#1e1e1e",
            "Goldman Sachs": "#000000",
            "State Street": "#008748",
            "Morgan Stanley": "#0070af",
            "Citibank": "#002d72",
            "HSBC": "#db0011",
            "Deloitte": "#86BC25",
            "EY": "#FFE600",
            "Northern Trust": "#001c5e",
            "Deutsche Bank": "#0018a8",
            "BNY Mellon": "#007dc3"
        }
        
        # Default color for sources not in the list
        default_color = "#6c757d"
        
        # Create modern HTML with better styling
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
                
                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}
                
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f8f9fa;
                    padding: 0;
                    margin: 0;
                }}
                
                .container {{
                    max-width: 680px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                }}
                
                .header {{
                    text-align: center;
                    padding: 30px 0;
                    border-bottom: 1px solid #eaeaea;
                    margin-bottom: 30px;
                }}
                
                .logo {{
                    font-size: 28px;
                    font-weight: 800;
                    color: #111;
                    margin-bottom: 10px;
                }}
                
                .headline {{
                    font-size: 24px;
                    font-weight: 700;
                    color: #111;
                    margin-bottom: 5px;
                }}
                
                .subheadline {{
                    font-size: 16px;
                    color: #555;
                    margin-bottom: 20px;
                }}
                
                .stats-container {{
                    display: flex;
                    justify-content: center;
                    margin: 20px 0;
                    flex-wrap: wrap;
                }}
                
                .stat-box {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px 25px;
                    margin: 0 10px 10px 0;
                    text-align: center;
                }}
                
                .stat-number {{
                    font-size: 22px;
                    font-weight: 700;
                    color: #111;
                }}
                
                .stat-label {{
                    font-size: 14px;
                    color: #555;
                }}
                
                .section-heading {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #111;
                    margin: 30px 0 15px 0;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #f1f1f1;
                    position: relative;
                }}
                
                .source-indicator {{
                    display: inline-block;
                    width: 18px;
                    height: 18px;
                    border-radius: 50%;
                    margin-right: 10px;
                    vertical-align: middle;
                }}
                
                .source-count {{
                    font-size: 16px;
                    color: #555;
                    font-weight: 500;
                    margin-left: 5px;
                }}
                
                .job-card {{
                    border: 1px solid #eaeaea;
                    border-radius: 10px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
                    transition: transform 0.2s, box-shadow 0.2s;
                    background-color: #ffffff;
                    position: relative;
                    overflow: hidden;
                }}
                
                .job-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.05);
                }}
                
                .job-card::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 5px;
                    height: 100%;
                    background-color: var(--source-color, #6c757d);
                }}
                
                .job-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #111;
                    margin-top: 0;
                    margin-bottom: 10px;
                }}
                
                .job-company {{
                    font-weight: 600;
                    font-size: 15px;
                    color: #444;
                    margin: 5px 0;
                }}
                
                .job-details-row {{
                    display: flex;
                    align-items: center;
                    margin: 10px 0;
                    flex-wrap: wrap;
                }}
                
                .job-detail {{
                    display: flex;
                    align-items: center;
                    font-size: 14px;
                    color: #555;
                    margin-right: 15px;
                    margin-bottom: 5px;
                }}
                
                .job-detail-icon {{
                    width: 16px;
                    height: 16px;
                    margin-right: 6px;
                    opacity: 0.7;
                }}
                
                .job-link {{
                    display: inline-block;
                    background-color: #f8f9fa;
                    color: #111 !important;
                    font-weight: 600;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none !important;
                    margin-top: 10px;
                    font-size: 14px;
                    border: 1px solid #eaeaea;
                    transition: all 0.2s ease;
                }}
                
                .job-link:hover {{
                    background-color: #f1f1f1;
                    border-color: #d5d5d5;
                }}
                
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #eaeaea;
                    text-align: center;
                    font-size: 14px;
                    color: #777;
                }}
                
                .date-label {{
                    display: inline-block;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 3px 10px;
                    border-radius: 20px;
                    background-color: #f1f5fa;
                    color: #555;
                }}
                
                @media (max-width: 600px) {{
                    .container {{
                        padding: 15px;
                    }}
                    
                    .job-title {{
                        font-size: 16px;
                    }}
                    
                    .job-company {{
                        font-size: 14px;
                    }}
                    
                    .job-link {{
                        width: 100%;
                        text-align: center;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">JobHunter</div>
                    <h1 class="headline">Hi PUU, {len(jobs_df)} finance jobs for you!</h1>
                    <p class="subheadline">The latest finance & banking positions in Bangalore</p>
                    
                    <div class="stats-container">
                        <div class="stat-box">
                            <div class="stat-number">{len(jobs_df)}</div>
                            <div class="stat-label">Total Jobs</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">{len(jobs_df['source'].unique())}</div>
                            <div class="stat-label">Sources</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number">7</div>
                            <div class="stat-label">Days Recent</div>
                        </div>
                    </div>
                </div>
        """
        
        # Group by source
        grouped = jobs_df.groupby('source')
        
        # Loop through each source
        for source, group in grouped:
            source_color = source_colors.get(source, default_color)
            html += f'''
                <div class="section-heading">
                    <span class="source-indicator" style="background-color: {source_color};"></span>
                    {source} <span class="source-count">({len(group)} jobs)</span>
                </div>
            '''
            
            # Loop through each job in the group
            for i, (_, job) in enumerate(group.iterrows(), 1):
                # Get original link for debugging
                original_link = job['link'] if 'link' in job else "No link provided"
                
                # Ensure link is valid
                link = self._validate_link(original_link)
                
                # Format location
                location = job['location']
                if location and len(location) > 25:
                    location = location[:22] + "..."
                
                # Format date
                date = job['date']
                
                # Determine if job is recent (today or yesterday)
                is_recent = any(term in date.lower() for term in ['today', 'just now', 'hour', 'minute', 'yesterday', '1 day'])
                date_class = "date-recent" if is_recent else ""
                
                html += f'''
                <div class="job-card" style="--source-color: {source_color};">
                    <h3 class="job-title">{i}. {job['title']}</h3>
                    <p class="job-company">{job['company']}</p>
                    
                    <div class="job-details-row">
                        <span class="job-detail">
                            <svg class="job-detail-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
                                <path d="M215.7 499.2C267 435 384 279.4 384 192C384 86 298 0 192 0S0 86 0 192c0 87.4 117 243 168.3 307.2c12.3 15.3 35.1 15.3 47.4 0zM192 256c-35.3 0-64-28.7-64-64s28.7-64 64-64s64 28.7 64 64s-28.7 64-64 64z"/>
                            </svg>
                            {location}
                        </span>
                        
                        <span class="job-detail">
                            <svg class="job-detail-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
                                <path d="M256 0a256 256 0 1 1 0 512A256 256 0 1 1 256 0zM232 120V256c0 8 4 15.5 10.7 20l96 64c11 7.4 25.9 4.4 33.3-6.7s4.4-25.9-6.7-33.3L280 243.2V120c0-13.3-10.7-24-24-24s-24 10.7-24 24z"/>
                            </svg>
                            <span class="{date_class}">{date}</span>
                        </span>
                    </div>
                    
                    <a href="{link}" target="_blank" class="job-link">View Job Details →</a>
                </div>
                '''
        
        # Add footer with timestamp and app info
        html += f'''
                <div class="footer">
                    <p>Job search completed on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
                    <p>This email was automatically generated by JobHunter</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html