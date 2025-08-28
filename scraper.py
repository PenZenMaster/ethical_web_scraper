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
from datetime import datetime
import time

from browser import BrowserManager
from image_manager import ImageManager
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
# Import validator modules
from validators import URLValidator, RobotsValidator, ContentValidator
# Import rate limiting modules
from rate_limiting import DomainLimiter


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
    image_info: Optional[Dict[str, Any]] = field(default_factory=dict)
    
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
        
        
        
        # Initialize image manager
        self.image_manager = ImageManager(self.config)
        
        # Initialize validators
        self.url_validator = URLValidator(self.config, self.logger)
        self.robots_validator = RobotsValidator(self.config, self.logger)
        self.content_validator = ContentValidator(self.config, self.logger)
        
        # Initialize rate limiter
        self.domain_limiter = DomainLimiter(self.config, self.logger)
        
        self.logger.info(f"EthicalScraper initialized - Robots respect: {self.respect_robots}")
        self.logger.info(f"Rate limiting - Max requests per domain per minute: {self.domain_limiter._max_requests_per_domain_per_minute}")
        self.logger.info(f"Image handling mode: {self.image_manager.handling_mode}")

    def _extract_alt_texts(self, html_content: str, image_urls: List[str]) -> Dict[str, str]:
        """
        Extract alt text for images from HTML content.
        
        Args:
            html_content: Full HTML content of the page
            image_urls: List of image URLs found in content
            
        Returns:
            Dict mapping image URLs to alt text
        """
        from bs4 import BeautifulSoup
        alt_texts = {}
        
        try:
            # Parse HTML to find img tags
            soup = BeautifulSoup(html_content, 'html.parser')
            
            for img_tag in soup.find_all('img'):
                src = img_tag.get('src')
                alt = img_tag.get('alt')
                
                if src and alt:
                    # Try to match with processed URLs (absolute URLs)
                    for url in image_urls:
                        if src in url or url.endswith(src.split('/')[-1]):
                            alt_texts[url] = alt
                            break
                            
        except Exception as e:
            self.logger.debug(f"Failed to extract alt texts: {e}")
            
        return alt_texts

    def validate_url(self, url: str) -> bool:
        """
        Validate URL format and accessibility using URLValidator.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
            
        Raises:
            ValidationException: If URL is invalid
        """
        return self.url_validator.validate(url)

    async def validate_robots_txt(self, url: str) -> bool:
        """
        Check if URL is allowed by robots.txt using RobotsValidator.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed by robots.txt
            
        Raises:
            RobotsException: If robots.txt disallows the URL
        """
        return await self.robots_validator.validate(url)

    async def check_domain_rate_limit(self, url: str) -> bool:
        """
        Check and enforce domain-level rate limiting using DomainLimiter.
        
        Args:
            url: URL to check for rate limiting
            
        Returns:
            True if request is allowed
            
        Raises:
            RateLimitException: If domain rate limit is exceeded
        """
        return await self.domain_limiter.check_rate_limit(url)

    def validate_content(self, content: ScrapedContent) -> bool:
        """
        Validate scraped content against configuration rules using ContentValidator.
        
        Args:
            content: ScrapedContent instance to validate
            
        Returns:
            True if content is valid
            
        Raises:
            ValidationException: If content validation fails
        """
        return self.content_validator.validate(content)

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
                    
                    # Process images using ImageManager
                    image_mapping = {}
                    processed_content_html = content_html
                    image_stats = {}
                    
                    if images:
                        # Create alt text mapping (could be extracted from original HTML)
                        alt_texts = self._extract_alt_texts(html_content, images)
                        
                        # Process images according to configuration
                        image_mapping = self.image_manager.process_images(images, alt_texts)
                        
                        # Update HTML content with new image URLs if needed
                        processed_content_html = self.image_manager.update_html_content(content_html, image_mapping)
                        
                        # Get image processing statistics
                        image_stats = self.image_manager.get_statistics()
                    
                    # Create scraped content object
                    scraped_content = ScrapedContent(
                        title=page_metadata.get('title', 'Untitled'),
                        slug=get_slug_from_title(page_metadata.get('title', url)),
                        source_url=url,
                        content_html=processed_content_html,
                        images=images,
                        scraped_at=get_timestamp(),
                        metadata={
                            **page_metadata,
                            'selector': selector,
                            'scrape_duration': round(time.time() - start_time, 2),
                            'image_count': len(images),
                            'content_length': len(processed_content_html),
                            'image_processing': image_stats,
                            **kwargs.get('metadata', {})
                        },
                        image_info={url: info.to_dict() for url, info in image_mapping.items()}
                    )
                    
                    # Step 4: Validate content
                    self.validate_content(scraped_content)
                    
                    # Enhanced logging with image processing info
                    image_summary = ""
                    if image_stats:
                        processed = image_stats.get('images_successful', 0)
                        total = image_stats.get('images_attempted', 0)
                        image_summary = f", images: {processed}/{total} processed"
                    
                    self.logger.info(
                        f"Scrape completed: {url} "
                        f"({len(processed_content_html)} chars, {len(images)} images found"
                        f"{image_summary}, {round(time.time() - start_time, 2)}s)"
                    )
                    
                    return scraped_content
                    
                finally:
                    await page.close()
                    
        except (ValidationException, RobotsException, NetworkException, 
                RenderException, SelectorException, RateLimitException) as e:
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