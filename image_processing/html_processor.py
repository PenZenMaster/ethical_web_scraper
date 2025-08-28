"""
Module/Script Name: html_processor.py
Path: ethical_web_scraper/image_processing/html_processor.py

Description:
HTML processing functionality extracted from image_manager.py for better modularity.
Handles HTML content updates for image URL replacements.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ImageManager.update_html_content method
"""

import logging
from pathlib import Path
from typing import Dict, Any


class HTMLProcessor:
    """Handles HTML content processing for image URL updates."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize HTML processor.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get configuration
        self.image_config = config.get('image_settings', {})
        self.output_config = config.get('output', {})
        
        # Get handling mode
        self.handling_mode = self.output_config.get('image_handling', 'absolute_urls')
        
        # Base directory for relative path calculations
        self.base_directory = Path(self.image_config.get('download_directory', 'images'))
    
    def update_html_content(self, html_content: str, image_mapping: Dict[str, Any]) -> str:
        """
        Update HTML content to use local/rehosted image URLs.
        
        Args:
            html_content: Original HTML content
            image_mapping: Dict mapping original URLs to ImageInfo objects
            
        Returns:
            Updated HTML content with new image URLs
        """
        updated_html = html_content
        replacement_count = 0
        
        for original_url, image_info in image_mapping.items():
            if hasattr(image_info, 'downloaded') and image_info.downloaded and hasattr(image_info, 'local_path') and image_info.local_path:
                # Determine new URL based on handling mode
                new_url = self._get_replacement_url(original_url, image_info)
                
                # Replace in HTML content
                if self._replace_in_html(updated_html, original_url, new_url):
                    updated_html = self._replace_in_html(updated_html, original_url, new_url, apply=True)
                    replacement_count += 1
        
        if replacement_count > 0:
            self.logger.info(f"Updated {replacement_count} image URLs in HTML content")
        
        return updated_html
    
    def _get_replacement_url(self, original_url: str, image_info: Any) -> str:
        """
        Get the replacement URL based on handling mode.
        
        Args:
            original_url: Original image URL
            image_info: ImageInfo object
            
        Returns:
            New URL to use in HTML
        """
        if self.handling_mode == 'download_and_rehost':
            # Use local path relative to output directory
            if hasattr(image_info, 'local_path') and image_info.local_path:
                try:
                    return str(Path(image_info.local_path).relative_to(self.base_directory.parent))
                except ValueError:
                    # If relative path calculation fails, use local path
                    return image_info.local_path
            
        elif self.handling_mode == 'download_local':
            # Use local file path
            if hasattr(image_info, 'local_path') and image_info.local_path:
                return image_info.local_path
        
        # Keep original URL as fallback
        return original_url
    
    def _replace_in_html(self, html_content: str, original_url: str, new_url: str, apply: bool = False) -> str:
        """
        Replace image URL in HTML content or check if replacement is possible.
        
        Args:
            html_content: HTML content to process
            original_url: Original URL to replace
            new_url: New URL to use
            apply: If True, apply replacement; if False, just check if possible
            
        Returns:
            Updated HTML content if apply=True, original content if apply=False
            For apply=False, returns truthy value if replacement is possible
        """
        # Try different quote styles
        replacements = [
            (f'src="{original_url}"', f'src="{new_url}"'),
            (f"src='{original_url}'", f"src='{new_url}'"),
        ]
        
        if apply:
            updated_html = html_content
            for old, new in replacements:
                updated_html = updated_html.replace(old, new)
            return updated_html
        else:
            # Check if any replacement is possible
            for old, _ in replacements:
                if old in html_content:
                    return True
            return False