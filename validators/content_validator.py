"""
Module/Script Name: content_validator.py
Path: ethical_web_scraper/validators/content_validator.py

Description:
Content validation functionality extracted from scraper.py for better modularity.
Validates scraped content against configuration rules.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from scraper.py validate_content method
"""

import logging
from typing import Dict, Any, List

from .base_validator import BaseValidator
from exceptions import ValidationException, handle_exception
from utils import validate_url


class ContentValidator(BaseValidator):
    """Validates scraped content against configuration rules."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize content validator.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        super().__init__(config, logger)
        
        # Get validation configuration
        self.validation_config = config.get('validation', {})
        self.min_content_length = self.validation_config.get('min_content_length', 100)
        self.max_content_length = self.validation_config.get('max_content_length', 1048576)
        self.required_fields = self.validation_config.get('required_fields', ['title', 'content_html'])
        self.image_url_validation = self.validation_config.get('image_url_validation', True)
        
    def validate(self, content) -> bool:
        """
        Validate scraped content against configuration rules.
        
        Args:
            content: ScrapedContent instance to validate
            
        Returns:
            True if content is valid
            
        Raises:
            ValidationException: If content validation fails
        """
        # Check required fields
        for field in self.required_fields:
            if not hasattr(content, field) or not getattr(content, field):
                exc = ValidationException(
                    f"Required field '{field}' is missing or empty",
                    validation_type="required_field",
                    expected_value=f"non-empty {field}",
                    actual_value=getattr(content, field, None)
                )
                handle_exception(exc, self.logger)
        
        # Check content length
        content_length = len(content.content_html)
        if content_length < self.min_content_length:
            exc = ValidationException(
                f"Content too short: {content_length} < {self.min_content_length} chars",
                validation_type="content_length",
                expected_value=f">= {self.min_content_length}",
                actual_value=content_length
            )
            handle_exception(exc, self.logger)
        
        if content_length > self.max_content_length:
            exc = ValidationException(
                f"Content too long: {content_length} > {self.max_content_length} chars",
                validation_type="content_length", 
                expected_value=f"<= {self.max_content_length}",
                actual_value=content_length
            )
            handle_exception(exc, self.logger)
        
        # Validate image URLs if enabled
        if self.image_url_validation and hasattr(content, 'images'):
            for img_url in content.images:
                if not validate_url(img_url):
                    self.logger.warning(f"Invalid image URL: {img_url}")
        
        self._log_validation_result(True, f"Content validation passed for {content.source_url}")
        return True