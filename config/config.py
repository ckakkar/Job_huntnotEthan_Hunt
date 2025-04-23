"""Configuration for job search parameters."""

# Job search keywords - add or remove as needed
JOB_KEYWORDS = [
    "regulatory reporting",
    "investment operations",
    "project manager",
    "program manager", 
    "finance operations",
    "risk analyst",
    "business analyst",
    "financial analyst",
    "operations analyst",
    "data analyst",
    "compliance officer",
    "financial controller",
    "reporting specialist",
    "investment banking",
    "portfolio manager",
    "treasury analyst",
    "product manager",
    "client servicing",
    "relationship manager",
    "investment specialist",
    "credit risk analyst",
    "associate",
    "manager"
]

# Location keywords
LOCATIONS = ["Bengaluru", "Bangalore", "Bangaluru", "Remote", "Hybrid Bangalore"]

# Company career pages to check
COMPANY_CAREER_PAGES = [
    {
        "name": "JPMorgan",
        "url": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?location=Bengaluru%2C+Karnataka%2C+India&locationId=300000000106947&lastSelectedFacet=POSTING_DATES",
        "dynamic": True
    },
    {
        "name": "State Street",
        "url": "https://statestreet.wd1.myworkdayjobs.com/en-US/Global/jobs?locations=be03a623dbe601d38a65c3391d4d1970",
        "dynamic": True
    },
    {
        "name": "Goldman Sachs",
        "url": "https://www.goldmansachs.com/careers/professionals/positions-for-experienced-professionals.html?city=Bengaluru",
        "dynamic": True
    },
    {
        "name": "Citi",
        "url": "https://jobs.citi.com/search-jobs/Bangalore%2C%20India/287/4/287-91-25931/12x97-13x06/500/2",
        "dynamic": True
    },
    {
        "name": "Morgan Stanley",
        "url": "https://www.morganstanley.com/careers/career-search.html?city=Bangalore",
        "dynamic": True
    },
    {
        "name": "HSBC",
        "url": "https://www.hsbc.com/careers/find-a-job?locationContains=Bangalore",
        "dynamic": True
    },
    {
        "name": "Deloitte",
        "url": "https://apply.deloitte.com/careers/SearchJobs/Bangalore?",
        "dynamic": True
    },
    {
        "name": "EY",
        "url": "https://careers.ey.com/ey/search/?location=Bangalore",
        "dynamic": True
    }
]

# Job portal configurations
JOB_PORTALS = [
    {
        "name": "Indeed",
        "enabled": True,
        "url_template": "https://in.indeed.com/jobs?q={keywords}&l={location}&fromage=7",
        "dynamic": False
    },
    {
        "name": "Naukri",
        "enabled": True,
        "url_template": "https://www.naukri.com/jobs-in-{location}?keywordsearch={keywords}&experience=0&nignbevent_src=jobsearchDesk&jobAge=7",
        "dynamic": True
    },
    {
        "name": "Foundit",
        "enabled": True,
        "url_template": "https://www.foundit.in/srp/results?keyword={keywords}&location={location}&sort=0&flow=default&experienceMin=0&experienceMax=30&postDate=7",
        "dynamic": True
    },
    {
        "name": "LinkedIn",
        "enabled": True,
        "url_template": "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_TPR=r604800",
        "dynamic": True
    },
    {
        "name": "TimesJobs",
        "enabled": True,
        "url_template": "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={keywords}&txtLocation={location}",
        "dynamic": True
    },
    {
        "name": "Shine",
        "enabled": True,
        "url_template": "https://www.shine.com/job-search/{keywords}-jobs-in-{location}",
        "dynamic": True
    }
]

# Maximum number of jobs to scrape per source
MAX_JOBS_PER_SOURCE = 50

# Delay between requests (in seconds) to avoid rate limiting
REQUEST_DELAY = 2

# User agent to use for requests
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"