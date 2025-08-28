"""
Module/Script Name: download_rehost_handler.py
Path: ethical_web_scraper/image_processing/format_handlers/download_rehost_handler.py

Description:
Handler for download_and_rehost mode - downloads images and prepares them for rehosting.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Handler for download_and_rehost mode (WordPress migration)
"""

from .download_local_handler import DownloadLocalHandler


class DownloadRehostHandler(DownloadLocalHandler):
    """Handler for download_and_rehost mode - extends local download for rehosting prep."""
    
    def process_images(self, image_urls, alt_texts=None):
        """
        Process images in download_and_rehost mode.
        
        This mode is essentially the same as download_local but may have
        different HTML processing behavior in the future.
        """
        # Use parent implementation for now
        results = super().process_images(image_urls, alt_texts)
        
        # Log the specific mode
        if results:
            self.logger.info(f"Images prepared for rehosting: {len(results)} processed")
        
        return results