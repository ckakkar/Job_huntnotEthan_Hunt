# scrapers/__init__.py
"""
Scrapers package for job hunting.

This package contains scrapers for various job portals and company career pages.
"""
from scrapers.indeed import IndeedScraper
from scrapers.naukri import NaukriScraper
from scrapers.foundit import FounditScraper
from scrapers.company_careers import get_company_scrapers