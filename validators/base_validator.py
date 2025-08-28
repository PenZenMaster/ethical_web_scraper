"""
Module/Script Name: base_validator.py
Path: ethical_web_scraper/validators/base_validator.py

Description:
Base validator class providing common validation functionality and interface.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Base class for all validator modules
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseValidator(ABC):
    """Base class for all validators providing common functionality."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize base validator.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def validate(self, *args, **kwargs) -> bool:
        """
        Abstract validation method to be implemented by subclasses.
        
        Returns:
            True if validation passes
            
        Raises:
            ValidationException: If validation fails
        """
        pass
    
    def _log_validation_result(self, result: bool, message: str, level: str = "debug") -> None:
        """
        Log validation results consistently.
        
        Args:
            result: Validation result
            message: Log message
            level: Log level (debug, info, warning, error)
        """
        log_method = getattr(self.logger, level, self.logger.debug)
        status = "PASSED" if result else "FAILED"
        log_method(f"Validation {status}: {message}")