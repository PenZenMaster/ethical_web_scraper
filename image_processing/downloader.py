"""
Module/Script Name: downloader.py
Path: ethical_web_scraper/image_processing/downloader.py

Description:
Image downloading functionality extracted from image_manager.py for better modularity.
Handles HTTP requests, content validation, and error handling for image downloads.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ImageManager.download_image method
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from exceptions import ValidationException


class ImageDownloader:
    """Handles image downloading with proper error handling and validation."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize image downloader.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get configuration
        self.image_config = config.get('image_settings', {})
        self.browser_config = config.get('browser', {})
        
        # Request settings
        self.timeout = self.image_config.get('timeout', 30)
        self.user_agent = self.browser_config.get('user_agent', 'EthicalScraper/1.0')
        
        # Size limits
        self.max_file_size = self._parse_size(self.image_config.get('max_image_size', '5MB'))
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string like '5MB' to bytes."""
        if isinstance(size_str, int):
            return size_str
            
        size_str = size_str.upper().strip()
        if size_str.endswith('MB'):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith('KB'):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith('GB'):
            return int(float(size_str[:-2]) * 1024 * 1024 * 1024)
        else:
            return int(size_str)
    
    def validate_url(self, url: str) -> bool:
        """
        Validate image URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
            
        Raises:
            ValidationException: If URL is invalid
        """
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationException(f"Invalid image URL: {url}")
        return True
    
    def download(self, url: str) -> Dict[str, Any]:
        """
        Download image content from URL.
        
        Args:
            url: Image URL to download
            
        Returns:
            Dict with download results including content, content_type, etc.
            
        Raises:
            ValidationException: If URL or content validation fails
            URLError, HTTPError: If download fails
        """
        # Validate URL
        self.validate_url(url)
        
        # Create request with proper headers
        request = Request(url, headers={
            'User-Agent': self.user_agent,
            'Accept': 'image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Download image
        self.logger.info(f"Downloading image: {url}")
        
        with urlopen(request, timeout=self.timeout) as response:
            # Check response
            if response.getcode() != 200:
                raise HTTPError(url, response.getcode(), f"HTTP {response.getcode()}", response.headers, None)
            
            # Get content info
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            content_length = int(response.headers.get('Content-Length', 0))
            
            # Validate content type
            if not content_type.startswith('image/'):
                self.logger.warning(f"Non-image content type for {url}: {content_type}")
            
            # Check file size limit
            if content_length > self.max_file_size:
                raise ValidationException(f"Image too large: {content_length} > {self.max_file_size}")
            
            # Download content
            content = response.read()
            actual_size = len(content)
            
            self.logger.info(f"Image content downloaded: {url} ({actual_size} bytes)")
            
            return {
                'content': content,
                'content_type': content_type,
                'size': actual_size,
                'url': url
            }