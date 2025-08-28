"""
Module/Script Name: rate_limiting/__init__.py
Path: ethical_web_scraper/rate_limiting/__init__.py

Description:
Rate limiting modules for domain-based request throttling and request tracking.
Provides ethical rate limiting to prevent overwhelming servers.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from scraper.py for better modularity
"""

from .domain_limiter import DomainLimiter
from .request_tracker import RequestTracker

__all__ = [
    'DomainLimiter',
    'RequestTracker'
]