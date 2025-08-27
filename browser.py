"""
Module/Script Name: browser.py
Path: ethical_web_scraper/browser.py

Description:
Browser management module for the Ethical Web Scraper project using Playwright
for JavaScript rendering and page automation.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-27

Comments:
* v1.00 - Initial implementation with async Playwright integration and configuration support
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse, urljoin
import time

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import centralized exceptions
from exceptions import NetworkException, RenderException, ConfigurationError


class BrowserManager:
    """
    Manages Playwright browser instances for web scraping with configuration support.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize browser manager with configuration.
        
        Args:
            config: Configuration dictionary with browser settings
        """
        self.config = config
        self.browser_config = config.get('browser', {})
        self.scraping_config = config.get('scraping', {})
        self.logger = logging.getLogger('ethical_web_scraper.browser')
        
        # Browser instances
        self._playwright = None
        self._browser = None
        self._context = None
        
        # Configuration values
        self.headless = self.browser_config.get('headless', True)
        self.timeout = self.browser_config.get('timeout', 30000)
        self.user_agent = self.browser_config.get('user_agent', 'EthicalScraper/1.0')
        self.viewport = self.browser_config.get('viewport', {'width': 1920, 'height': 1080})
        self.delay_between_requests = self.scraping_config.get('delay_between_requests', 2.0)
        
        self.logger.info(f"BrowserManager initialized - Headless: {self.headless}, Timeout: {self.timeout}ms")

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self) -> None:
        """
        Start the browser instance and create context.
        """
        try:
            self._playwright = await async_playwright().start()
            
            # Launch browser with configuration
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
                ]
            )
            
            # Create browser context with configuration
            self._context = await self._browser.new_context(
                viewport=self.viewport,
                user_agent=self.user_agent,
                ignore_https_errors=True,
                java_script_enabled=True
            )
            
            # Set default timeout
            self._context.set_default_timeout(self.timeout)
            
            self.logger.info("Browser started successfully")
            
        except PlaywrightError as e:
            self.logger.error(f"Failed to start browser: {e}")
            raise RenderException(f"Browser startup failed: {e}", browser_error=str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error starting browser: {e}")
            raise RenderException(f"Unexpected browser error: {e}")

    async def close(self) -> None:
        """
        Close browser instance and cleanup resources.
        """
        try:
            if self._context:
                await self._context.close()
                self._context = None
                
            if self._browser:
                await self._browser.close()
                self._browser = None
                
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
                
            self.logger.info("Browser closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((NetworkException, RenderException))
    )
    async def get_page(self, url: str, wait_for: Optional[str] = None) -> Page:
        """
        Create a new page and navigate to URL with retry logic.
        
        Args:
            url: URL to navigate to
            wait_for: Optional selector to wait for after page load
            
        Returns:
            Playwright Page instance
            
        Raises:
            NetworkException: If navigation fails
            RenderException: If page rendering fails
        """
        if not self._context:
            raise RenderException("Browser not started. Call start() first.")
        
        try:
            # Apply rate limiting
            if self.delay_between_requests > 0:
                await asyncio.sleep(self.delay_between_requests)
            
            page = await self._context.new_page()
            
            # Navigate with timeout
            self.logger.info(f"Navigating to: {url}")
            response = await page.goto(url, timeout=self.timeout)
            
            if not response:
                raise NetworkException(f"No response received for URL: {url}", url=url)
            
            # Check response status
            if response.status >= 400:
                self.logger.warning(f"HTTP {response.status} for URL: {url}")
                if response.status >= 500:
                    raise NetworkException(f"Server error {response.status} for URL: {url}", 
                                         url=url, status_code=response.status)
            
            # Wait for network idle (JavaScript execution complete)
            await page.wait_for_load_state("networkidle", timeout=self.timeout)
            
            # Optional: wait for specific selector
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=5000)
                except Exception as e:
                    self.logger.warning(f"Selector '{wait_for}' not found within timeout: {e}")
            
            self.logger.info(f"Page loaded successfully: {url}")
            return page
            
        except asyncio.TimeoutError:
            self.logger.error(f"Timeout loading page: {url}")
            raise NetworkException(f"Timeout loading page: {url}", url=url)
        except PlaywrightError as e:
            self.logger.error(f"Playwright error for {url}: {e}")
            raise RenderException(f"Page rendering failed: {e}", url=url, browser_error=str(e))
        except Exception as e:
            self.logger.error(f"Unexpected error loading {url}: {e}")
            raise RenderException(f"Unexpected page error: {e}", url=url)

    async def render_content(self, page: Page, timeout: int = 30000) -> str:
        """
        Get fully rendered HTML content from page.
        
        Args:
            page: Playwright Page instance
            timeout: Timeout in milliseconds
            
        Returns:
            Rendered HTML content
            
        Raises:
            RenderException: If content rendering fails
        """
        try:
            # Wait for any dynamic content to load
            await page.wait_for_timeout(1000)  # Brief pause for dynamic content
            
            # Get rendered HTML
            content = await page.content()
            
            if not content or len(content.strip()) < 100:
                raise RenderException("Rendered content appears empty or too short")
            
            self.logger.info(f"Content rendered successfully - {len(content)} characters")
            return content
            
        except Exception as e:
            self.logger.error(f"Error rendering content: {e}")
            raise RenderException(f"Content rendering failed: {e}")

    async def get_page_title(self, page: Page) -> str:
        """
        Get page title.
        
        Args:
            page: Playwright Page instance
            
        Returns:
            Page title string
        """
        try:
            title = await page.title()
            return title.strip() if title else "Untitled"
        except Exception as e:
            self.logger.warning(f"Error getting page title: {e}")
            return "Untitled"

    async def get_page_metadata(self, page: Page) -> Dict[str, Any]:
        """
        Extract page metadata (title, description, etc.).
        
        Args:
            page: Playwright Page instance
            
        Returns:
            Dictionary containing page metadata
        """
        metadata = {}
        
        try:
            # Get title
            metadata['title'] = await self.get_page_title(page)
            
            # Get meta description
            try:
                desc_element = await page.query_selector('meta[name="description"]')
                if desc_element:
                    metadata['description'] = await desc_element.get_attribute('content') or ''
            except:
                metadata['description'] = ''
            
            # Get canonical URL
            try:
                canonical_element = await page.query_selector('link[rel="canonical"]')
                if canonical_element:
                    metadata['canonical_url'] = await canonical_element.get_attribute('href') or ''
            except:
                metadata['canonical_url'] = ''
            
            # Get current URL
            metadata['url'] = page.url
            
            self.logger.debug(f"Page metadata extracted: {metadata}")
            
        except Exception as e:
            self.logger.warning(f"Error extracting page metadata: {e}")
        
        return metadata

    async def screenshot(self, page: Page, path: str = None) -> bytes:
        """
        Take screenshot of current page.
        
        Args:
            page: Playwright Page instance
            path: Optional file path to save screenshot
            
        Returns:
            Screenshot bytes
        """
        try:
            screenshot_bytes = await page.screenshot(
                path=path,
                full_page=True,
                type='png'
            )
            
            if path:
                self.logger.info(f"Screenshot saved to: {path}")
            else:
                self.logger.info(f"Screenshot captured - {len(screenshot_bytes)} bytes")
                
            return screenshot_bytes
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            raise RenderException(f"Screenshot failed: {e}")

    def is_running(self) -> bool:
        """
        Check if browser is running.
        
        Returns:
            True if browser is active
        """
        return self._browser is not None and self._context is not None


# Convenience functions for backward compatibility
async def load_rendered_html(url: str, config: Dict[str, Any] = None, timeout: int = 15000) -> tuple[str, str]:
    """
    Load and render HTML content from URL (backward compatibility function).
    
    Args:
        url: URL to load
        config: Optional configuration dictionary
        timeout: Timeout in milliseconds
        
    Returns:
        Tuple of (content, title)
    """
    if config is None:
        config = {
            'browser': {'headless': True, 'timeout': timeout},
            'scraping': {'delay_between_requests': 0}
        }
    
    async with BrowserManager(config) as browser_manager:
        page = await browser_manager.get_page(url)
        try:
            content = await browser_manager.render_content(page)
            title = await browser_manager.get_page_title(page)
            return content, title
        finally:
            await page.close()


def load_rendered_html_sync(url: str, config: Dict[str, Any] = None, timeout: int = 15000) -> tuple[str, str]:
    """
    Synchronous wrapper for load_rendered_html.
    
    Args:
        url: URL to load
        config: Optional configuration dictionary
        timeout: Timeout in milliseconds
        
    Returns:
        Tuple of (content, title)
    """
    return asyncio.run(load_rendered_html(url, config, timeout))