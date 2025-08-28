"""
Module/Script Name: image_manager.py
Path: ethical_web_scraper/image_manager.py

Description:
Advanced image management system for downloading, storing, and processing images
during web scraping operations. Refactored to use modular components for better
separation of concerns.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Refactored to use modular image processing components
* v1.01 - Initial implementation for EWS-010 image management capabilities
"""

import logging
from typing import Dict, List, Optional, Any

from image_processing import HTMLProcessor
from image_processing.format_handlers import (
    AbsoluteUrlsHandler,
    DownloadLocalHandler, 
    DownloadRehostHandler
)


class ImageManager:
    """
    Manages image downloading, storage, and processing for web scraping operations.
    
    Supports multiple image handling modes:
    - absolute_urls: Convert to absolute URLs only (v1.00 behavior)
    - download_local: Download images to local directory
    - download_and_rehost: Download + prepare for rehosting
    - base64: Embed small images as base64 data
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ImageManager with configuration.
        
        Args:
            config: Configuration dictionary containing image settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Get configuration sections
        self.output_config = config.get('output', {})
        self.image_config = config.get('image_settings', {})
        
        # Image handling mode
        self.handling_mode = self.output_config.get('image_handling', 'absolute_urls')
        
        # Initialize HTML processor
        self.html_processor = HTMLProcessor(config, self.logger)
        
        # Initialize handlers
        self.handlers = {
            'absolute_urls': AbsoluteUrlsHandler(config, self.logger),
            'download_local': DownloadLocalHandler(config, self.logger),
            'download_and_rehost': DownloadRehostHandler(config, self.logger)
        }
        
        self.logger.info(f"ImageManager initialized with handling mode: {self.handling_mode}")
    
    def process_images(self, image_urls: List[str], alt_texts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process multiple image URLs according to handling mode.
        
        Args:
            image_urls: List of image URLs to process
            alt_texts: Dict mapping URLs to alt text
            
        Returns:
            Dict mapping original URLs to ImageInfo objects
        """
        if not image_urls:
            return {}
        
        # Get the appropriate handler
        handler = self.handlers.get(self.handling_mode)
        if not handler:
            if self.handling_mode == 'base64':
                self.logger.warning(f"base64 mode not yet implemented, falling back to absolute_urls")
                handler = self.handlers['absolute_urls']
            else:
                self.logger.error(f"Unknown image handling mode: {self.handling_mode}")
                handler = self.handlers['absolute_urls']
        
        # Process images using the handler
        return handler.process_images(image_urls, alt_texts)
    
    def update_html_content(self, html_content: str, image_mapping: Dict[str, Any]) -> str:
        """
        Update HTML content to use local/rehosted image URLs.
        
        Args:
            html_content: Original HTML content
            image_mapping: Dict mapping original URLs to ImageInfo
            
        Returns:
            Updated HTML content with new image URLs
        """
        return self.html_processor.update_html_content(html_content, image_mapping)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics from the current handler.
        
        Returns:
            Dictionary with processing statistics
        """
        handler = self.handlers.get(self.handling_mode)
        if handler and hasattr(handler, 'stats'):
            stats = handler.stats
            return {
                'images_attempted': stats.get('attempted', 0),
                'images_successful': stats.get('successful', 0),
                'images_failed': stats.get('failed', 0),
                'images_skipped': stats.get('skipped', 0),
                'total_downloaded_size': stats.get('total_size', 0),
                'success_rate': (stats.get('successful', 0) / max(1, stats.get('attempted', 1))) * 100,
                'handling_mode': self.handling_mode
            }
        else:
            return {
                'images_attempted': 0,
                'images_successful': 0,
                'images_failed': 0,
                'images_skipped': 0,
                'total_downloaded_size': 0,
                'success_rate': 0,
                'handling_mode': self.handling_mode
            }
    
    def cleanup_failed_downloads(self):
        """Remove any incomplete or failed download files."""
        # Delegate to storage manager in download handlers
        handler = self.handlers.get(self.handling_mode)
        if handler and hasattr(handler, 'storage_manager'):
            return handler.storage_manager.cleanup_failed_downloads()
        return 0


# Maintain backward compatibility
def process_images_legacy(image_urls: List[str], config: Dict[str, Any]) -> List[str]:
    """
    Legacy function to maintain compatibility with v1.00 behavior.
    
    Args:
        image_urls: List of image URLs
        config: Configuration dictionary
        
    Returns:
        List of processed image URLs (absolute URLs)
    """
    return image_urls  # v1.00 behavior - just return URLs as-is


# Re-export ImageInfo from handlers for backward compatibility
from image_processing.format_handlers.absolute_urls_handler import ImageInfo