"""
Enterprise Brochure Generator - Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Configuration
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", os.getenv("OPENAI_API_BASE", None))

# Crawler settings
DEFAULT_MAX_CRAWL_PAGES = int(os.getenv("MAX_CRAWL_PAGES", "5"))
BROWSER_TIMEOUT_MS = int(os.getenv("BROWSER_TIMEOUT_MS", "30000"))
HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

# High-priority keywords to prioritize enterprise brochure content during link discovery
PRIORITY_URL_KEYWORDS = [
    "about",
    "company",
    "services",
    "solutions",
    "products",
    "pricing",
    "features",
    "contact",
    "platform",
    "why-us",
]

# Irrelevant URL patterns to exclude
EXCLUDE_URL_PATTERNS = [
    r"/blog/",
    r"/tag/",
    r"/category/",
    r"/author/",
    r"/terms",
    r"/privacy",
    r"/legal",
    r"/cookie",
    r"/login",
    r"/signin",
    r"/signup",
    r"\.pdf$",
    r"\.png$",
    r"\.jpg$",
    r"\.jpeg$",
    r"\.svg$",
    r"\.zip$",
]
