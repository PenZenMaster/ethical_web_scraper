"""
Module/Script Name: format_handlers/__init__.py
Path: ethical_web_scraper/image_processing/format_handlers/__init__.py

Description:
Format-specific handlers for different image processing modes and operations.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Format-specific handlers for modular image processing
"""

from .base_handler import BaseImageHandler
from .absolute_urls_handler import AbsoluteUrlsHandler
from .download_local_handler import DownloadLocalHandler
from .download_rehost_handler import DownloadRehostHandler

__all__ = [
    'BaseImageHandler',
    'AbsoluteUrlsHandler',
    'DownloadLocalHandler',
    'DownloadRehostHandler'
]