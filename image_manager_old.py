"""
Module/Script Name: image_manager.py
Path: ethical_web_scraper/image_manager.py

Description:
Advanced image management system for downloading, storing, and processing images
during web scraping operations. Supports multiple storage modes including local
download, rehosting, and WordPress media library integration.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-27

Comments:
* v1.01 - Initial implementation for EWS-010 image management capabilities
"""

import os
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urljoin
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import time
import json

from exceptions import ValidationException, NetworkException, handle_exception


class ImageInfo:
    """Information about a downloaded/processed image."""
    
    def __init__(
        self, 
        original_url: str,
        local_path: Optional[str] = None,
        rehost_url: Optional[str] = None,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        dimensions: Optional[Tuple[int, int]] = None,
        alt_text: Optional[str] = None,
        downloaded: bool = False,
        error: Optional[str] = None
    ):
        self.original_url = original_url
        self.local_path = local_path
        self.rehost_url = rehost_url
        self.file_size = file_size
        self.mime_type = mime_type
        self.dimensions = dimensions
        self.alt_text = alt_text
        self.downloaded = downloaded
        self.error = error
        self.filename = Path(local_path).name if local_path else None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'original_url': self.original_url,
            'local_path': self.local_path,
            'rehost_url': self.rehost_url,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'dimensions': self.dimensions,
            'alt_text': self.alt_text,
            'filename': self.filename,
            'downloaded': self.downloaded,
            'error': self.error
        }


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
        self.output_config = config.get('output', {})
        self.image_config = config.get('image_settings', {})
        
        # Image handling mode
        self.handling_mode = self.output_config.get('image_handling', 'absolute_urls')
        
        # Directory settings
        self.base_directory = Path(self.image_config.get('download_directory', 'images'))
        self.organize_by_domain = self.image_config.get('organize_by_domain', True)
        
        # Size and format limits
        self.max_file_size = self._parse_size(self.image_config.get('max_image_size', '5MB'))
        self.allowed_formats = self.image_config.get('allowed_formats', ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'])
        
        # Processing options
        self.create_thumbnails = self.image_config.get('create_thumbnails', False)
        self.optimize_images = self.image_config.get('optimize', False)
        self.quality = self.image_config.get('quality', 85)
        
        # Request settings
        self.timeout = self.image_config.get('timeout', 30)
        self.user_agent = config.get('browser', {}).get('user_agent', 'EthicalScraper/1.0')
        
        # WordPress integration
        self.wordpress_upload = self.image_config.get('wordpress_upload', False)
        
        self.logger = logging.getLogger(__name__)
        
        # Download statistics
        self.stats = {
            'attempted': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'total_size': 0
        }
    
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
    
    def _get_safe_filename(self, url: str, content_type: Optional[str] = None) -> str:
        """
        Generate a safe filename from URL and content type.
        
        Args:
            url: Original image URL
            content_type: MIME type of the image
            
        Returns:
            Safe filename for local storage
        """
        parsed = urlparse(url)
        
        # Try to get filename from URL path
        path = Path(parsed.path)
        if path.suffix and path.name:
            base_name = path.stem
            extension = path.suffix.lower()
        else:
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            base_name = f"image_{url_hash}"
            
            # Determine extension from content type
            if content_type:
                extension = mimetypes.guess_extension(content_type) or '.bin'
            else:
                extension = '.jpg'  # Default fallback
        
        # Clean the base name
        base_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_')).strip()
        if not base_name:
            base_name = f"image_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            
        return f"{base_name}{extension}"
    
    def _get_storage_path(self, url: str, filename: str) -> Path:
        """
        Get the full storage path for an image.
        
        Args:
            url: Original image URL
            filename: Safe filename
            
        Returns:
            Path where image should be stored
        """
        if self.organize_by_domain:
            domain = urlparse(url).netloc or 'unknown'
            # Clean domain name for directory
            domain = "".join(c for c in domain if c.isalnum() or c in ('-', '.')).strip()
            return self.base_directory / domain / filename
        else:
            return self.base_directory / filename
    
    def download_image(self, url: str, alt_text: Optional[str] = None) -> ImageInfo:
        """
        Download a single image from URL.
        
        Args:
            url: Image URL to download
            alt_text: Alt text from img tag
            
        Returns:
            ImageInfo object with download results
        """
        self.stats['attempted'] += 1
        
        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationException(f"Invalid image URL: {url}")
            
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
                
                # Generate filename and storage path
                filename = self._get_safe_filename(url, content_type)
                storage_path = self._get_storage_path(url, filename)
                
                # Ensure directory exists
                storage_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download and save
                content = response.read()
                actual_size = len(content)
                
                with open(storage_path, 'wb') as f:
                    f.write(content)
                
                self.stats['successful'] += 1
                self.stats['total_size'] += actual_size
                
                self.logger.info(f"Image downloaded: {storage_path} ({actual_size} bytes)")
                
                return ImageInfo(
                    original_url=url,
                    local_path=str(storage_path),
                    file_size=actual_size,
                    mime_type=content_type,
                    alt_text=alt_text,
                    downloaded=True
                )
                
        except (URLError, HTTPError, OSError, ValidationException) as e:
            self.stats['failed'] += 1
            error_msg = f"Failed to download {url}: {e}"
            self.logger.error(error_msg)
            
            return ImageInfo(
                original_url=url,
                alt_text=alt_text,
                downloaded=False,
                error=str(e)
            )
        except Exception as e:
            self.stats['failed'] += 1
            error_msg = f"Unexpected error downloading {url}: {e}"
            self.logger.error(error_msg)
            
            return ImageInfo(
                original_url=url,
                alt_text=alt_text,
                downloaded=False,
                error=str(e)
            )
    
    def process_images(self, image_urls: List[str], alt_texts: Optional[Dict[str, str]] = None) -> Dict[str, ImageInfo]:
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
        
        alt_texts = alt_texts or {}
        results = {}
        
        self.logger.info(f"Processing {len(image_urls)} images in '{self.handling_mode}' mode")
        
        for i, url in enumerate(image_urls, 1):
            if self.handling_mode == 'absolute_urls':
                # v1.00 behavior - just ensure absolute URLs
                results[url] = ImageInfo(
                    original_url=url,
                    alt_text=alt_texts.get(url),
                    downloaded=False
                )
                
            elif self.handling_mode in ('download_local', 'download_and_rehost'):
                # Download images locally
                alt_text = alt_texts.get(url)
                image_info = self.download_image(url, alt_text)
                results[url] = image_info
                
                # Add delay between downloads to be respectful
                if i < len(image_urls):  # Don't delay after last image
                    time.sleep(0.5)
                    
            elif self.handling_mode == 'base64':
                # TODO: Implement base64 embedding for small images
                self.logger.warning(f"base64 mode not yet implemented, falling back to absolute_urls")
                results[url] = ImageInfo(
                    original_url=url,
                    alt_text=alt_texts.get(url),
                    downloaded=False
                )
            
            else:
                self.logger.warning(f"Unknown image handling mode: {self.handling_mode}")
                results[url] = ImageInfo(
                    original_url=url,
                    alt_text=alt_texts.get(url),
                    downloaded=False,
                    error=f"Unknown handling mode: {self.handling_mode}"
                )
        
        self._log_statistics()
        return results
    
    def update_html_content(self, html_content: str, image_mapping: Dict[str, ImageInfo]) -> str:
        """
        Update HTML content to use local/rehosted image URLs.
        
        Args:
            html_content: Original HTML content
            image_mapping: Dict mapping original URLs to ImageInfo
            
        Returns:
            Updated HTML content with new image URLs
        """
        updated_html = html_content
        
        for original_url, image_info in image_mapping.items():
            if image_info.downloaded and image_info.local_path:
                # For WordPress, we might want to use relative paths or rehost URLs
                if self.handling_mode == 'download_and_rehost':
                    # Use local path relative to output directory
                    new_url = str(Path(image_info.local_path).relative_to(self.base_directory.parent))
                elif self.handling_mode == 'download_local':
                    # Use local file path
                    new_url = image_info.local_path
                else:
                    # Keep original URL
                    new_url = original_url
                
                # Replace in HTML content
                updated_html = updated_html.replace(f'src="{original_url}"', f'src="{new_url}"')
                updated_html = updated_html.replace(f"src='{original_url}'", f"src='{new_url}'")
        
        return updated_html
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics."""
        return {
            'images_attempted': self.stats['attempted'],
            'images_successful': self.stats['successful'], 
            'images_failed': self.stats['failed'],
            'images_skipped': self.stats['skipped'],
            'total_downloaded_size': self.stats['total_size'],
            'success_rate': (self.stats['successful'] / max(1, self.stats['attempted'])) * 100,
            'handling_mode': self.handling_mode
        }
    
    def _log_statistics(self):
        """Log current download statistics."""
        stats = self.get_statistics()
        self.logger.info(
            f"Image processing stats: {stats['images_successful']}/{stats['images_attempted']} successful "
            f"({stats['success_rate']:.1f}%), {stats['total_downloaded_size']} bytes downloaded"
        )
    
    def cleanup_failed_downloads(self):
        """Remove any incomplete or failed download files."""
        if not self.base_directory.exists():
            return
            
        cleanup_count = 0
        for file_path in self.base_directory.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size == 0:
                try:
                    file_path.unlink()
                    cleanup_count += 1
                except OSError:
                    pass
        
        if cleanup_count > 0:
            self.logger.info(f"Cleaned up {cleanup_count} empty/failed download files")


# Convenience function for backward compatibility
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