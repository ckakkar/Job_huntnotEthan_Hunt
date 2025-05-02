"""Configuration for job search parameters."""

# Job search keywords - enhanced for finance and banking roles
JOB_KEYWORDS = [
    "regulatory reporting",
    "investment operations",
    "project manager finance",
    "program manager finance", 
    "finance operations",
    "risk analyst",
    "business analyst finance",
    "financial analyst",
    "operations analyst",
    "data analyst finance",
    "compliance officer",
    "financial controller",
    "reporting specialist",
    "investment banking",
    "portfolio manager",
    "treasury analyst",
    "product manager finance",
    "client servicing finance",
    "relationship manager",
    "investment specialist",
    "credit risk analyst",
    "associate finance",
    "manager finance",
    "finance operations",
    "KYC analyst",
    "AML analyst",
    "regulatory compliance",
    "fund accounting",
    "financial reporting",
    "equity research",
    "banking operations"
]

# Location keywords
LOCATIONS = ["Bengaluru", "Bangalore", "Bangaluru", "Remote", "Hybrid Bangalore"]

# Company career pages to check with OpenAI
COMPANY_CAREER_PAGES = [
    {
        "name": "JPMorgan",
        "url": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?location=Bengaluru%2C+Karnataka%2C+India&locationId=300000000106947&lastSelectedFacet=POSTING_DATES"
    },
    {
        "name": "State Street",
        "url": "https://statestreet.wd1.myworkdayjobs.com/en-US/Global/jobs?locations=be03a623dbe601d38a65c3391d4d1970"
    },
    {
        "name": "Goldman Sachs",
        "url": "https://www.goldmansachs.com/careers/professionals/positions-for-experienced-professionals.html?city=Bengaluru"
    },
    {
        "name": "Citi",
        "url": "https://jobs.citi.com/search-jobs/Bangalore%2C%20India/287/4/287-91-25931/12x97-13x06/500/2"
    },
    {
        "name": "Morgan Stanley",
        "url": "https://www.morganstanley.com/careers/career-search.html?city=Bangalore"
    },
    {
        "name": "HSBC",
        "url": "https://www.hsbc.com/careers/find-a-job?locationContains=Bangalore"
    },
    {
        "name": "Deloitte",
        "url": "https://apply.deloitte.com/careers/SearchJobs/Bangalore?"
    },
    {
        "name": "EY",
        "url": "https://careers.ey.com/ey/search/?location=Bangalore"
    },
    {
        "name": "KPMG", 
        "url": "https://kpmgcareers.com/jobsearch/?location=Bangalore"
    },
    {
        "name": "Deutsche Bank",
        "url": "https://careers.db.com/professionals/search-roles?location=Bangalore"
    },
    {
        "name": "BNY Mellon",
        "url": "https://jobs.bnymellon.com/jobs?keywords=&location=Bangalore"
    },
    {
        "name": "Northern Trust",
        "url": "https://careers.northerntrust.com/jobs/search/17313739"
    },
    {
        "name": "Barclays",
        "url": "https://search.jobs.barclays/search-jobs/Bangalore"
    },
    {
        "name": "Credit Suisse",
        "url": "https://tas-creditsuisse.taleo.net/careersection/external_jobdescription/jobsearch.ftl?lang=en&location=Bangalore"
    }
]

# Job portal configurations - now simplified for API-based access
JOB_PORTALS = [
    {
        "name": "Indeed",
        "enabled": True,
        "url_template": "https://in.indeed.com/jobs?q={keywords}&l={location}&fromage=7"
    },
    {
        "name": "Naukri",
        "enabled": True,
        "url_template": "https://www.naukri.com/jobs-in-{location}?keywordsearch={keywords}&experience=0&jobAge=7"
    },
    {
        "name": "Foundit",
        "enabled": True,
        "url_template": "https://www.foundit.in/srp/results?keyword={keywords}&location={location}&sort=0&postDate=7"
    },
    {
        "name": "LinkedIn",
        "enabled": True,
        "url_template": "https://www.linkedin.com/jobs/search/?keywords={keywords}&location={location}&f_TPR=r604800"
    },
    {
        "name": "TimesJobs",
        "enabled": True,
        "url_template": "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={keywords}&txtLocation={location}"
    },
    {
        "name": "Shine",
        "enabled": True,
        "url_template": "https://www.shine.com/job-search/{keywords}-jobs-in-{location}"
    },
    {
        "name": "SimplyHired",
        "enabled": True,
        "url_template": "https://www.simplyhired.co.in/search?q={keywords}&l={location}"
    },
    # Finance-specific job portals
    {
        "name": "eFinancialCareers",
        "enabled": True,
        "url_template": "https://www.efinancialcareers.com/jobs-Finance-Accounting-Bangalore.s016.1.g2020"
    },
    {
        "name": "CFOIndia",
        "enabled": True,
        "url_template": "https://www.cfo-india.in/cfo-jobs/location/bangalore/"
    }
]

# Maximum number of jobs to scrape per source
MAX_JOBS_PER_SOURCE = 50

# Delay between requests (in seconds) to avoid rate limiting
REQUEST_DELAY = 2

# User agent to use for requests - newer version
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"