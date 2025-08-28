"""
Module/Script Name: image_processing/__init__.py
Path: ethical_web_scraper/image_processing/__init__.py

Description:
Image processing modules for downloading, storage management, HTML processing,
and format-specific handlers. Provides modular image handling components.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from image_manager.py for better modularity
"""

from .downloader import ImageDownloader
from .storage_manager import StorageManager
from .html_processor import HTMLProcessor

__all__ = [
    'ImageDownloader',
    'StorageManager',
    'HTMLProcessor'
]