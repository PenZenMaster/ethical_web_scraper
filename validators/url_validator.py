"""
Module/Script Name: url_validator.py
Path: ethical_web_scraper/validators/url_validator.py

Description:
URL validation functionality extracted from scraper.py for better modularity.
Handles URL format validation and accessibility checks.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from scraper.py validate_url method
"""

import logging
from typing import Dict, Any
from urllib.parse import urlparse

from .base_validator import BaseValidator
from exceptions import ValidationException, handle_exception
from utils import validate_url


class URLValidator(BaseValidator):
    """Validates URL format and accessibility."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize URL validator.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        super().__init__(config, logger)
        
        # Get validation configuration
        self.validation_config = config.get('validation', {})
        self.allowed_schemes = self.validation_config.get('allowed_schemes', ['http', 'https'])
        
    def validate(self, url: str) -> bool:
        """
        Validate URL format and accessibility.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid
            
        Raises:
            ValidationException: If URL is invalid
        """
        if not url or not isinstance(url, str):
            exc = ValidationException("URL must be a non-empty string", 
                                    validation_type="url_format")
            handle_exception(exc, self.logger)
        
        if not validate_url(url):
            exc = ValidationException(f"Invalid URL format: {url}", url=url, 
                                    validation_type="url_format")
            handle_exception(exc, self.logger)
        
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                exc = ValidationException(f"URL missing domain: {url}", url=url,
                                        validation_type="url_format")
                handle_exception(exc, self.logger)
            
            if parsed.scheme not in self.allowed_schemes:
                exc = ValidationException(f"Unsupported URL scheme: {parsed.scheme}", 
                                        url=url, validation_type="url_scheme")
                handle_exception(exc, self.logger)
                
        except ValidationException:
            raise
        except Exception as e:
            exc = ValidationException(f"URL validation error: {e}", url=url,
                                    validation_type="url_parsing")
            handle_exception(exc, self.logger)
        
        self._log_validation_result(True, f"URL validation passed: {url}")
        return True