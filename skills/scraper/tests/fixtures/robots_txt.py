"""Robots.txt fixtures for scraper tests."""

ALLOW_ALL_ROBOTS = """
User-agent: *
Disallow:
"""

BLOCK_ALL_ROBOTS = """
User-agent: *
Disallow: /
"""

CRAWL_DELAY_ROBOTS = """
User-agent: base
Crawl-delay: 2
Disallow: /private/
"""

SPECIFIC_UA_ROBOTS = """
User-agent: base
Disallow: /blocked-for-base/

User-agent: other
Disallow: /blocked-for-other/
"""

NO_ROBOTS_FILE = None  # 404 response
