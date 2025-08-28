"""
Module/Script Name: request_tracker.py
Path: ethical_web_scraper/rate_limiting/request_tracker.py

Description:
Request tracking functionality for managing domain-level request history.
Tracks request timestamps and provides cleanup of old requests.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from scraper.py request tracking logic
"""

import time
import logging
from typing import Dict, List
from urllib.parse import urlparse


class RequestTracker:
    """Tracks request history for domain-level rate limiting."""
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize request tracker.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        self._domain_request_history: Dict[str, List[float]] = {}
    
    def get_domain(self, url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain string
        """
        parsed = urlparse(url)
        return parsed.netloc
    
    def cleanup_old_requests(self, domain: str, current_time: float, window_seconds: int = 60) -> None:
        """
        Remove request records older than the specified window.
        
        Args:
            domain: Domain to cleanup
            current_time: Current timestamp
            window_seconds: Time window to keep records for (default 60 seconds)
        """
        if domain in self._domain_request_history:
            self._domain_request_history[domain] = [
                req_time for req_time in self._domain_request_history[domain]
                if current_time - req_time < window_seconds
            ]
            self.logger.debug(f"Cleaned up old requests for domain {domain}")
    
    def get_recent_request_count(self, domain: str, current_time: float, window_seconds: int = 60) -> int:
        """
        Get count of recent requests for a domain.
        
        Args:
            domain: Domain to check
            current_time: Current timestamp
            window_seconds: Time window to check (default 60 seconds)
            
        Returns:
            Number of recent requests
        """
        # Cleanup old requests first
        self.cleanup_old_requests(domain, current_time, window_seconds)
        
        # Return count of recent requests
        return len(self._domain_request_history.get(domain, []))
    
    def record_request(self, url: str) -> None:
        """
        Record a new request for the domain.
        
        Args:
            url: URL being requested
        """
        domain = self.get_domain(url)
        current_time = time.time()
        
        if domain not in self._domain_request_history:
            self._domain_request_history[domain] = []
        
        self._domain_request_history[domain].append(current_time)
        self.logger.debug(f"Recorded request for domain {domain} at {current_time}")
    
    def get_domain_stats(self, domain: str) -> Dict[str, int]:
        """
        Get statistics for a domain.
        
        Args:
            domain: Domain to get stats for
            
        Returns:
            Dictionary with domain statistics
        """
        current_time = time.time()
        recent_count = self.get_recent_request_count(domain, current_time)
        total_count = len(self._domain_request_history.get(domain, []))
        
        return {
            'recent_requests': recent_count,
            'total_requests': total_count
        }