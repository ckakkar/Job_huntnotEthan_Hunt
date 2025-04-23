# JobHunter - Comprehensive Job Search Tool

JobHunter is an automated tool that searches for jobs across multiple sources, filters them based on your criteria, and sends you email notifications with all job postings from the last 24 hours.

## 🚀 Features

- **Multi-Source Search**: Indeed, LinkedIn, Naukri, Foundit, and company career pages
- **Multiple Methods**: Direct APIs, Selenium scraping, and OpenAI-powered extraction
- **Fallback Mechanisms**: If one method fails, others take over automatically
- **Optimized for Mac M2**: Special configurations for Apple Silicon
- **Beautifully Formatted Emails**: HTML emails with job details grouped by source
- **24-Hour Filter**: Focus on jobs posted in the last 24 hours

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- Google Chrome (for Selenium)
- Gmail account (for sending alerts)
- OpenAI API key (optional but recommended)

### Setup with Conda (Recommended for Mac M2)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/JobHunter.git
   cd JobHunter
   ```

2. **Create and activate conda environment**:
   ```bash
   conda create -n jobhunter python=3.11 -y
   conda activate jobhunter
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure ChromeDriver** (for Mac M2):
   ```bash
   brew install --cask chromedriver
   xattr -d com.apple.quarantine /usr/local/bin/chromedriver
   ```

5. **Set up environment variables**:
   Create a `.env` file in the project root with:
   ```
   # Email configuration (required)
   EMAIL_SENDER=your.email@gmail.com
   EMAIL_PASSWORD=your-app-password  # Generate from Google Account
   EMAIL_RECIPIENT=your.email@gmail.com
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587

   # OpenAI API (optional but recommended)
   OPENAI_API_KEY=your-openai-api-key
   ```

## 🚀 Usage

### Basic Usage
```bash
# Run the job search
python enhanced_main.py
```

### VS Code Integration
1. Open VS Code
2. Install Python extension
3. Use Command Palette (`Cmd+Shift+P`) to select your conda interpreter
4. Open the project and start coding

## 🧩 Project Structure
```
JobHunterApp/
├── apis/                  # Direct API integrations
│   ├── indeed_api.py      # Indeed API client
│   ├── linkedin_api.py    # LinkedIn API client
│   └── github_jobs_api.py # GitHub Jobs API client
├── scrapers/              # Web scrapers
│   ├── base_scraper.py    # Base scraper class
│   ├── indeed.py          # Indeed scraper
│   ├── naukri.py          # Naukri scraper
│   ├── foundit.py         # Foundit scraper
│   └── company_careers.py # Company career page scraper
├── alert/                 # Notification systems
│   └── email_alert.py     # Email alerts with HTML formatting
├── utils/                 # Utility functions
│   ├── data_processor.py  # Job data processing
│   └── webdriver_helper.py # WebDriver utilities for Mac M2
├── config/                # Configuration files
│   ├── config.py          # Search parameters
│   └── credentials.py     # Load credentials from .env
├── openai_scraper.py      # OpenAI-powered scraper
├── enhanced_main.py       # Main script
└── .env                   # Environment variables
```

## ✅ Customization

Edit `config/config.py` to customize:
- Job keywords
- Locations
- Company career pages
- Number of jobs to scrape per source

## 🔍 How It Works

JobHunter uses a multi-method approach to ensure reliable results:

1. **Direct APIs** (tried first):
   - Uses structured data extraction from Indeed, LinkedIn, etc.
   - Most reliable but limited by site structure

2. **Selenium-based Scraping** (if APIs fail):
   - Uses Chrome/Safari to render JavaScript-heavy sites
   - Optimized for Mac M2 architecture

3. **OpenAI-powered Extraction** (fallback):
   - Uses GPT-3.5-turbo to extract job data from HTML
   - Cost-efficient approach for hard-to-scrape sites

4. **Data Processing**:
   - Filters jobs by keywords, location, and posting date
   - Removes duplicates and sorts by recency
   - Creates a unified dataset from all sources

5. **Email Notification**:
   - Sends a beautifully formatted HTML email
   - Groups jobs by source for easy browsing

## 📧 Gmail Setup

To use Gmail for sending alerts:
1. Enable 2-Step Verification in your Google Account
2. Generate an App Password: 
   - Go to your Google Account
   - Select Security
   - Select 2-Step Verification
   - Scroll down to App passwords
   - Generate a new password for "Mail"
3. Use this password in your `.env` file

## 🧠 OpenAI Integration

The OpenAI integration helps scrape sites with complex structures by:
1. Extracting the raw HTML
2. Sending it to GPT-3.5-turbo with instructions to identify job listings
3. Parsing the structured response into job data

This approach is used as a fallback when other methods fail, keeping costs minimal while ensuring comprehensive results.

## 🐞 Troubleshooting

- **ChromeDriver Issues**: Run the commands in step 4 of the installation
- **Email Sending Failed**: Make sure you're using an App Password, not your regular password
- **No Jobs Found**: Try broadening your search keywords in `config.py`
- **Selenium Errors**: The app will automatically fall back to API and OpenAI methods

## 📝 License

MIT License

## 🙏 Acknowledgements

- OpenAI for GPT-3.5-turbo API
- Selenium and ChromeDriver projects
- BeautifulSoup and Pandas libraries