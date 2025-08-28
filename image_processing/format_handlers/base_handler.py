"""
Module/Script Name: base_handler.py
Path: ethical_web_scraper/image_processing/format_handlers/base_handler.py

Description:
Base class for image processing handlers providing common functionality.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Base handler class for image processing modes
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseImageHandler(ABC):
    """Base class for image processing handlers."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize base handler.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.image_config = config.get('image_settings', {})
    
    @abstractmethod
    def process_images(self, image_urls: List[str], alt_texts: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Process images according to the handler's specific mode.
        
        Args:
            image_urls: List of image URLs to process
            alt_texts: Optional mapping of URLs to alt text
            
        Returns:
            Dictionary mapping URLs to ImageInfo objects
        """
        pass
    
    def _log_processing_start(self, image_urls: List[str], mode: str) -> None:
        """Log the start of image processing."""
        self.logger.info(f"Processing {len(image_urls)} images in '{mode}' mode")
    
    def _log_processing_complete(self, results: Dict[str, Any], mode: str) -> None:
        """Log completion of image processing."""
        successful = sum(1 for info in results.values() 
                        if hasattr(info, 'downloaded') and info.downloaded)
        total = len(results)
        self.logger.info(f"Completed {mode} processing: {successful}/{total} successful")