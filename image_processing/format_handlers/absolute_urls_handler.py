"""
Module/Script Name: absolute_urls_handler.py
Path: ethical_web_scraper/image_processing/format_handlers/absolute_urls_handler.py

Description:
Handler for absolute URLs mode - maintains v1.00 behavior with no actual downloading.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Handler for absolute_urls mode (legacy v1.00 behavior)
"""

import logging
from typing import Dict, List, Optional, Any

from .base_handler import BaseImageHandler


class ImageInfo:
    """Minimal ImageInfo for absolute URLs mode."""
    
    def __init__(self, original_url: str, alt_text: Optional[str] = None):
        self.original_url = original_url
        self.alt_text = alt_text
        self.downloaded = False
        self.local_path = None
        self.error = None
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_url': self.original_url,
            'alt_text': self.alt_text,
            'downloaded': self.downloaded,
            'local_path': self.local_path,
            'error': self.error
        }


class AbsoluteUrlsHandler(BaseImageHandler):
    """Handler for absolute URLs mode - no downloading, just URL processing."""
    
    def process_images(self, image_urls: List[str], alt_texts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process images in absolute_urls mode (v1.00 behavior).
        
        Args:
            image_urls: List of image URLs to process
            alt_texts: Optional mapping of URLs to alt text
            
        Returns:
            Dictionary mapping URLs to ImageInfo objects
        """
        if not image_urls:
            return {}
        
        alt_texts = alt_texts or {}
        results = {}
        
        self._log_processing_start(image_urls, 'absolute_urls')
        
        for url in image_urls:
            # v1.00 behavior - just ensure absolute URLs
            results[url] = ImageInfo(
                original_url=url,
                alt_text=alt_texts.get(url)
            )
        
        self._log_processing_complete(results, 'absolute_urls')
        return results