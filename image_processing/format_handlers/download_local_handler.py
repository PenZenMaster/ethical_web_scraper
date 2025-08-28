"""
Module/Script Name: download_local_handler.py
Path: ethical_web_scraper/image_processing/format_handlers/download_local_handler.py

Description:
Handler for download_local mode - downloads images to local storage.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Handler for download_local mode
"""

import time
import logging
from typing import Dict, List, Optional, Any

from .base_handler import BaseImageHandler
from ..downloader import ImageDownloader
from ..storage_manager import StorageManager


class ImageInfo:
    """ImageInfo for download operations."""
    
    def __init__(
        self,
        original_url: str,
        local_path: Optional[str] = None,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        alt_text: Optional[str] = None,
        downloaded: bool = False,
        error: Optional[str] = None
    ):
        self.original_url = original_url
        self.local_path = local_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.alt_text = alt_text
        self.downloaded = downloaded
        self.error = error
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'original_url': self.original_url,
            'local_path': self.local_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'alt_text': self.alt_text,
            'downloaded': self.downloaded,
            'error': self.error
        }


class DownloadLocalHandler(BaseImageHandler):
    """Handler for download_local mode - downloads images to local storage."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """Initialize handler with downloader and storage manager."""
        super().__init__(config, logger)
        self.downloader = ImageDownloader(config, logger)
        self.storage_manager = StorageManager(config, logger)
        
        # Statistics
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'total_size': 0
        }
    
    def process_images(self, image_urls: List[str], alt_texts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process images in download_local mode.
        
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
        
        self._log_processing_start(image_urls, 'download_local')
        
        for i, url in enumerate(image_urls, 1):
            alt_text = alt_texts.get(url)
            image_info = self._download_single_image(url, alt_text)
            results[url] = image_info
            
            # Add delay between downloads to be respectful
            if i < len(image_urls):  # Don't delay after last image
                time.sleep(0.5)
        
        self._log_processing_complete(results, 'download_local')
        self._log_statistics()
        return results
    
    def _download_single_image(self, url: str, alt_text: Optional[str] = None) -> ImageInfo:
        """Download a single image."""
        self.stats['attempted'] += 1
        
        try:
            # Download image content
            download_result = self.downloader.download(url)
            
            # Generate filename and storage path
            filename = self.storage_manager.get_safe_filename(url, download_result['content_type'])
            storage_path = self.storage_manager.get_storage_path(url, filename)
            
            # Save content
            self.storage_manager.save_content(download_result['content'], storage_path)
            
            # Update statistics
            self.stats['successful'] += 1
            self.stats['total_size'] += download_result['size']
            
            return ImageInfo(
                original_url=url,
                local_path=str(storage_path),
                file_size=download_result['size'],
                mime_type=download_result['content_type'],
                alt_text=alt_text,
                downloaded=True
            )
            
        except Exception as e:
            self.stats['failed'] += 1
            error_msg = f"Failed to download {url}: {e}"
            self.logger.error(error_msg)
            
            return ImageInfo(
                original_url=url,
                alt_text=alt_text,
                downloaded=False,
                error=str(e)
            )
    
    def _log_statistics(self):
        """Log download statistics."""
        success_rate = (self.stats['successful'] / max(1, self.stats['attempted'])) * 100
        self.logger.info(
            f"Download stats: {self.stats['successful']}/{self.stats['attempted']} successful "
            f"({success_rate:.1f}%), {self.stats['total_size']} bytes downloaded"
        )