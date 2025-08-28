"""
Module/Script Name: storage_manager.py
Path: ethical_web_scraper/image_processing/storage_manager.py

Description:
Storage management functionality extracted from image_manager.py for better modularity.
Handles file path generation, directory organization, and file system operations.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ImageManager storage methods
"""

import os
import hashlib
import mimetypes
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class StorageManager:
    """Manages file storage operations for downloaded images."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize storage manager.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get configuration
        self.image_config = config.get('image_settings', {})
        
        # Directory settings
        self.base_directory = Path(self.image_config.get('download_directory', 'images'))
        self.organize_by_domain = self.image_config.get('organize_by_domain', True)
        
        # Format settings
        self.allowed_formats = self.image_config.get('allowed_formats', ['jpg', 'jpeg', 'png', 'webp', 'gif', 'svg'])
    
    def get_safe_filename(self, url: str, content_type: Optional[str] = None) -> str:
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
    
    def get_storage_path(self, url: str, filename: str) -> Path:
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
    
    def ensure_directory(self, file_path: Path) -> None:
        """
        Ensure the directory for a file path exists.
        
        Args:
            file_path: Full path to file
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Ensured directory exists: {file_path.parent}")
    
    def save_content(self, content: bytes, file_path: Path) -> None:
        """
        Save binary content to file.
        
        Args:
            content: Binary content to save
            file_path: Path to save file at
        """
        # Ensure directory exists
        self.ensure_directory(file_path)
        
        # Write content
        with open(file_path, 'wb') as f:
            f.write(content)
        
        self.logger.info(f"Saved file: {file_path} ({len(content)} bytes)")
    
    def cleanup_failed_downloads(self) -> int:
        """
        Remove any incomplete or failed download files.
        
        Returns:
            Number of files cleaned up
        """
        if not self.base_directory.exists():
            return 0
            
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
        
        return cleanup_count