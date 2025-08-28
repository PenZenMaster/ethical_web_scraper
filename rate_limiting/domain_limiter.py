"""
Module/Script Name: domain_limiter.py
Path: ethical_web_scraper/rate_limiting/domain_limiter.py

Description:
Domain-level rate limiting functionality extracted from scraper.py for better modularity.
Enforces ethical request limits per domain to prevent overwhelming servers.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from scraper.py check_domain_rate_limit method
"""

import time
import logging
from typing import Dict, Any

from .request_tracker import RequestTracker
from exceptions import RateLimitException, handle_exception


class DomainLimiter:
    """Handles domain-level rate limiting to prevent overwhelming servers."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize domain limiter.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get rate limiting configuration
        self.scraping_config = config.get('scraping', {})
        self._max_requests_per_domain_per_minute = self.scraping_config.get(
            'max_requests_per_domain_per_minute', 20
        )
        
        # Initialize request tracker
        self.request_tracker = RequestTracker(logger)
    
    async def check_rate_limit(self, url: str) -> bool:
        """
        Check and enforce domain-level rate limiting.
        
        Args:
            url: URL to check for rate limiting
            
        Returns:
            True if request is allowed
            
        Raises:
            RateLimitException: If domain rate limit is exceeded
        """
        domain = self.request_tracker.get_domain(url)
        current_time = time.time()
        
        # Get recent request count
        recent_requests = self.request_tracker.get_recent_request_count(domain, current_time)
        
        # Check if we're exceeding rate limit
        if recent_requests >= self._max_requests_per_domain_per_minute:
            exc = RateLimitException(
                f"Rate limit exceeded for domain {domain}: {recent_requests} requests in last minute "
                f"(max: {self._max_requests_per_domain_per_minute})",
                url=url, 
                domain=domain, 
                current_rate=recent_requests
            )
            handle_exception(exc, self.logger)
        
        # Record this request
        self.request_tracker.record_request(url)
        
        self.logger.debug(
            f"Domain rate check passed - {domain}: {recent_requests + 1}/"
            f"{self._max_requests_per_domain_per_minute} requests in last minute"
        )
        return True
    
    def get_rate_limit_info(self, url: str) -> Dict[str, Any]:
        """
        Get rate limiting information for a domain.
        
        Args:
            url: URL to check
            
        Returns:
            Dictionary with rate limiting information
        """
        domain = self.request_tracker.get_domain(url)
        current_time = time.time()
        
        stats = self.request_tracker.get_domain_stats(domain)
        recent_requests = self.request_tracker.get_recent_request_count(domain, current_time)
        
        return {
            'domain': domain,
            'max_requests_per_minute': self._max_requests_per_domain_per_minute,
            'recent_requests': recent_requests,
            'remaining_requests': max(0, self._max_requests_per_domain_per_minute - recent_requests),
            'stats': stats
        }