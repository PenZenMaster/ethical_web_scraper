"""
Module/Script Name: robots_validator.py
Path: ethical_web_scraper/validators/robots_validator.py

Description:
Robots.txt validation functionality extracted from scraper.py for better modularity.
Handles robots.txt compliance checking with caching.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from scraper.py validate_robots_txt method
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from .base_validator import BaseValidator
from exceptions import RobotsException, handle_exception


class RobotsValidator(BaseValidator):
    """Validates robots.txt compliance with caching."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize robots validator.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        super().__init__(config, logger)
        
        # Get scraping configuration
        self.scraping_config = config.get('scraping', {})
        self.respect_robots = self.scraping_config.get('respect_robots', True)
        
        # Get browser configuration for user agent
        self.browser_config = config.get('browser', {})
        self.user_agent = self.browser_config.get('user_agent', 'EthicalScraper/1.0')
        
        # Robot cache for performance
        self._robots_cache: Dict[str, RobotFileParser] = {}
        
    async def validate(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed by robots.txt
            
        Raises:
            RobotsException: If robots.txt disallows the URL
        """
        if not self.respect_robots:
            self._log_validation_result(True, f"Robots.txt validation skipped (disabled): {url}")
            return True
        
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            # Check cache first
            if robots_url in self._robots_cache:
                rp = self._robots_cache[robots_url]
                self.logger.debug(f"Using cached robots.txt for {parsed.netloc}")
            else:
                # Download and parse robots.txt
                rp = RobotFileParser()
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self._robots_cache[robots_url] = rp
                    self.logger.debug(f"Robots.txt loaded for {parsed.netloc}")
                except Exception as e:
                    # If robots.txt doesn't exist or can't be read, allow scraping
                    self.logger.debug(f"No robots.txt found for {parsed.netloc}: {e}")
                    self._log_validation_result(True, f"No robots.txt found, allowing: {url}")
                    return True
            
            # Check if URL is allowed
            can_fetch = rp.can_fetch(self.user_agent, url)
            if not can_fetch:
                exc = RobotsException(
                    f"Robots.txt disallows scraping of {url} for user-agent {self.user_agent}",
                    url=url, user_agent=self.user_agent
                )
                handle_exception(exc, self.logger)
            
            self._log_validation_result(True, f"Robots.txt allows scraping: {url}")
            return True
            
        except RobotsException:
            raise
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If we can't check robots.txt, err on the side of caution but allow
            self._log_validation_result(True, f"Robots.txt check failed, allowing: {url}")
            return True