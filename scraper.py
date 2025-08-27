"""
Module/Script Name: scraper.py
Path: ethical_web_scraper/scraper.py

Description:
Core scraping module for the Ethical Web Scraper project with URL validation,
robots.txt compliance, and content extraction capabilities.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-27

Comments:
* v1.00 - Initial implementation with EthicalScraper class and URL validation
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urlparse, urljoin, urlunparse
from urllib.robotparser import RobotFileParser
from datetime import datetime
import time

from browser import BrowserManager
from utils import (
    extract_content, get_slug_from_title, validate_url, 
    get_timestamp
)
# Import centralized exceptions
from exceptions import (
    NetworkException, RenderException, SelectorException,
    ValidationException, RobotsException, RateLimitException, ConfigurationError,
    handle_exception
)


@dataclass
class ScrapedContent:
    """Data class representing scraped content from a web page."""
    title: str
    slug: str
    source_url: str
    content_html: str
    images: List[str]
    scraped_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate required fields after initialization."""
        if not self.title:
            self.title = "Untitled"
        if not self.scraped_at:
            self.scraped_at = get_timestamp()


class EthicalScraper:
    """
    Main scraper class that handles URL validation, robots.txt compliance,
    and content extraction with proper error handling.
    """
    
    def __init__(self, config: Union[str, Dict[str, Any]] = "config/default.yaml"):
        """
        Initialize the ethical scraper with configuration.
        
        Args:
            config: Either path to configuration file or config dictionary
        """
        from utils import load_config, setup_logging, get_environment_config, merge_configs
        
        # Handle both config path and config dict
        if isinstance(config, str):
            # Load and merge configurations
            base_config = load_config(config)
            env_config = get_environment_config()
            self.config = merge_configs(base_config, env_config)
        elif isinstance(config, dict):
            # Use provided config dict, merge with environment
            env_config = get_environment_config()
            self.config = merge_configs(config, env_config)
        else:
            raise TypeError("config must be either a string path or dictionary")
        
        # Setup logging
        self.logger = setup_logging(self.config)
        
        # Configuration sections
        self.scraping_config = self.config.get('scraping', {})
        self.validation_config = self.config.get('validation', {})
        self.browser_config = self.config.get('browser', {})
        
        # Scraping settings
        self.respect_robots = self.scraping_config.get('respect_robots', True)
        self.delay_between_requests = self.scraping_config.get('delay_between_requests', 2.0)
        self.retry_attempts = self.scraping_config.get('retry_attempts', 3)
        self.user_agent = self.browser_config.get('user_agent', 'EthicalScraper/1.0')
        
        # Validation settings
        self.min_content_length = self.validation_config.get('min_content_length', 100)
        self.max_content_length = self.validation_config.get('max_content_length', 1048576)
        self.required_fields = self.validation_config.get('required_fields', ['title', 'content_html'])
        
        # Robot cache for performance
        self._robots_cache: Dict[str, RobotFileParser] = {}
        
        # Ethical tracking for domain-level rate limiting
        self._domain_request_history: Dict[str, List[float]] = {}
        self._max_requests_per_domain_per_minute = self.scraping_config.get('max_requests_per_domain_per_minute', 20)
        
        self.logger.info(f"EthicalScraper initialized - Robots respect: {self.respect_robots}")
        self.logger.info(f"Rate limiting - Max requests per domain per minute: {self._max_requests_per_domain_per_minute}")

    def validate_url(self, url: str) -> bool:
        """
        Validate URL format and accessibility.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
            
        Raises:
            ValidationException: If URL is invalid
        """
        if not url or not isinstance(url, str):
            exc = ValidationException("URL must be a non-empty string", 
                                    validation_type="url_format")
            handle_exception(exc, self.logger)
        
        if not validate_url(url):
            exc = ValidationException(f"Invalid URL format: {url}", url=url, 
                                    validation_type="url_format")
            handle_exception(exc, self.logger)
        
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                exc = ValidationException(f"URL missing domain: {url}", url=url,
                                        validation_type="url_format")
                handle_exception(exc, self.logger)
            
            if parsed.scheme not in ['http', 'https']:
                exc = ValidationException(f"Unsupported URL scheme: {parsed.scheme}", 
                                        url=url, validation_type="url_scheme")
                handle_exception(exc, self.logger)
                
        except ValidationException:
            raise
        except Exception as e:
            exc = ValidationException(f"URL validation error: {e}", url=url,
                                    validation_type="url_parsing")
            handle_exception(exc, self.logger)
        
        return True

    async def validate_robots_txt(self, url: str) -> bool:
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
            return True
        
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            
            # Check cache first
            if robots_url in self._robots_cache:
                rp = self._robots_cache[robots_url]
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
                    return True
            
            # Check if URL is allowed
            can_fetch = rp.can_fetch(self.user_agent, url)
            if not can_fetch:
                exc = RobotsException(
                    f"Robots.txt disallows scraping of {url} for user-agent {self.user_agent}",
                    url=url, user_agent=self.user_agent
                )
                handle_exception(exc, self.logger)
            
            self.logger.debug(f"Robots.txt allows scraping: {url}")
            return True
            
        except RobotsException:
            raise
        except Exception as e:
            self.logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If we can't check robots.txt, err on the side of caution but allow
            return True

    async def check_domain_rate_limit(self, url: str) -> bool:
        """
        Check and enforce domain-level rate limiting to prevent overwhelming servers.
        
        Args:
            url: URL to check for rate limiting
            
        Returns:
            True if request is allowed, False if rate limited
            
        Raises:
            RateLimitException: If domain rate limit is exceeded
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        current_time = time.time()
        
        # Clean up old requests (older than 1 minute)
        if domain in self._domain_request_history:
            self._domain_request_history[domain] = [
                req_time for req_time in self._domain_request_history[domain]
                if current_time - req_time < 60  # Keep only last minute
            ]
        else:
            self._domain_request_history[domain] = []
        
        # Check if we're exceeding rate limit
        recent_requests = len(self._domain_request_history[domain])
        if recent_requests >= self._max_requests_per_domain_per_minute:
            exc = RateLimitException(
                f"Rate limit exceeded for domain {domain}: {recent_requests} requests in last minute (max: {self._max_requests_per_domain_per_minute})",
                url=url, domain=domain, current_rate=recent_requests
            )
            handle_exception(exc, self.logger)
        
        # Record this request
        self._domain_request_history[domain].append(current_time)
        
        self.logger.debug(f"Domain rate check passed - {domain}: {recent_requests + 1}/{self._max_requests_per_domain_per_minute} requests in last minute")
        return True

    def validate_content(self, content: ScrapedContent) -> bool:
        """
        Validate scraped content against configuration rules.
        
        Args:
            content: ScrapedContent instance to validate
            
        Returns:
            True if content is valid
            
        Raises:
            ValidationException: If content validation fails
        """
        # Check required fields
        for field in self.required_fields:
            if not hasattr(content, field) or not getattr(content, field):
                exc = ValidationException(
                    f"Required field '{field}' is missing or empty",
                    validation_type="required_field",
                    expected_value=f"non-empty {field}",
                    actual_value=getattr(content, field, None)
                )
                handle_exception(exc, self.logger)
        
        # Check content length
        content_length = len(content.content_html)
        if content_length < self.min_content_length:
            exc = ValidationException(
                f"Content too short: {content_length} < {self.min_content_length} chars",
                validation_type="content_length",
                expected_value=f">= {self.min_content_length}",
                actual_value=content_length
            )
            handle_exception(exc, self.logger)
        
        if content_length > self.max_content_length:
            exc = ValidationException(
                f"Content too long: {content_length} > {self.max_content_length} chars",
                validation_type="content_length", 
                expected_value=f"<= {self.max_content_length}",
                actual_value=content_length
            )
            handle_exception(exc, self.logger)
        
        # Validate image URLs if enabled
        if self.validation_config.get('image_url_validation', True):
            for img_url in content.images:
                if not validate_url(img_url):
                    self.logger.warning(f"Invalid image URL: {img_url}")
        
        self.logger.debug(f"Content validation passed for {content.source_url}")
        return True

    async def scrape_url(self, url: str, selector: str, **kwargs) -> ScrapedContent:
        """
        Scrape content from a single URL with full validation and error handling.
        
        Args:
            url: URL to scrape
            selector: CSS selector for content extraction
            **kwargs: Additional options (wait_for, metadata, etc.)
            
        Returns:
            ScrapedContent instance
            
        Raises:
            ValidationException: If URL or content validation fails
            RobotsException: If robots.txt disallows scraping
            NetworkException: If network request fails
            RenderException: If page rendering fails
            SelectorException: If selector not found
        """
        start_time = time.time()
        
        try:
            # Step 1: Validate URL
            self.logger.info(f"Starting scrape: {url}")
            self.validate_url(url)
            
            # Step 2: Check robots.txt
            await self.validate_robots_txt(url)
            
            # Step 3: Check domain rate limiting
            await self.check_domain_rate_limit(url)
            
            # Step 4: Scrape content using browser
            async with BrowserManager(self.config) as browser:
                # Get page with optional wait_for selector
                wait_for = kwargs.get('wait_for')
                page = await browser.get_page(url, wait_for=wait_for)
                
                try:
                    # Render content and get metadata
                    html_content = await browser.render_content(page)
                    page_metadata = await browser.get_page_metadata(page)
                    
                    # Extract content using selector
                    try:
                        content_html, images = extract_content(html_content, selector, url)
                    except ValueError as e:
                        exc = SelectorException(str(e), url=url, selector=selector)
                        handle_exception(exc, self.logger)
                    
                    # Create scraped content object
                    scraped_content = ScrapedContent(
                        title=page_metadata.get('title', 'Untitled'),
                        slug=get_slug_from_title(page_metadata.get('title', url)),
                        source_url=url,
                        content_html=content_html,
                        images=images,
                        scraped_at=get_timestamp(),
                        metadata={
                            **page_metadata,
                            'selector': selector,
                            'scrape_duration': round(time.time() - start_time, 2),
                            'image_count': len(images),
                            'content_length': len(content_html),
                            **kwargs.get('metadata', {})
                        }
                    )
                    
                    # Step 4: Validate content
                    self.validate_content(scraped_content)
                    
                    self.logger.info(
                        f"Scrape completed: {url} "
                        f"({len(content_html)} chars, {len(images)} images, "
                        f"{round(time.time() - start_time, 2)}s)"
                    )
                    
                    return scraped_content
                    
                finally:
                    await page.close()
                    
        except (ValidationException, RobotsException, NetworkException, 
                RenderException, SelectorException) as e:
            # These are already handled and logged by handle_exception
            raise
        except Exception as e:
            exc = RenderException(f"Unexpected scraping error: {e}", url=url)
            handle_exception(exc, self.logger)

    async def batch_scrape(self, urls: List[str], selector: str, **kwargs) -> List[ScrapedContent]:
        """
        Scrape multiple URLs with error handling and rate limiting.
        
        Args:
            urls: List of URLs to scrape
            selector: CSS selector for content extraction
            **kwargs: Additional options passed to scrape_url
            
        Returns:
            List of ScrapedContent instances (successful scrapes only)
        """
        results = []
        failed_urls = []
        
        self.logger.info(f"Starting batch scrape: {len(urls)} URLs")
        
        for i, url in enumerate(urls, 1):
            try:
                # Rate limiting between requests
                if i > 1 and self.delay_between_requests > 0:
                    await asyncio.sleep(self.delay_between_requests)
                
                result = await self.scrape_url(url, selector, **kwargs)
                results.append(result)
                
                self.logger.info(f"Progress: {i}/{len(urls)} completed")
                
            except Exception as e:
                failed_urls.append((url, str(e)))
                self.logger.warning(f"Failed to scrape {url}: {e}")
                continue
        
        if failed_urls:
            self.logger.warning(f"Failed to scrape {len(failed_urls)} URLs: {failed_urls}")
        
        self.logger.info(f"Batch scrape completed: {len(results)}/{len(urls)} successful")
        return results


# Convenience functions for backward compatibility
def scrape_url(url: str, selector: str, config_path: str = "config/default.yaml") -> ScrapedContent:
    """
    Synchronous convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        selector: CSS selector
        config_path: Path to configuration file
        
    Returns:
        ScrapedContent instance
    """
    scraper = EthicalScraper(config_path)
    return asyncio.run(scraper.scrape_url(url, selector))


async def scrape_url_async(url: str, selector: str, config_path: str = "config/default.yaml") -> ScrapedContent:
    """
    Async convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        selector: CSS selector
        config_path: Path to configuration file
        
    Returns:
        ScrapedContent instance
    """
    scraper = EthicalScraper(config_path)
    return await scraper.scrape_url(url, selector)