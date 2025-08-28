"""
Module/Script Name: base_exporter.py
Path: ethical_web_scraper/exporters/base_exporter.py

Description:
Base exporter class providing common export functionality and validation.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Base class for all export format handlers
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from exceptions import ValidationException, handle_exception


class ValidationResult:
    """Result of content validation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def __bool__(self) -> bool:
        return self.is_valid


class BaseExporter(ABC):
    """Base class for all exporters providing common functionality."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize base exporter.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        
        # Get configuration sections
        self.output_config = config.get('output', {})
        self.validation_config = config.get('validation', {})
        
        # Output settings
        self.include_metadata = self.output_config.get('include_metadata', True)
        self.default_output_dir = self.output_config.get('directory', 'output')
        
        # Validation settings
        self.required_fields = self.validation_config.get('required_fields', ['title', 'content_html'])
    
    @abstractmethod
    def export(self, content_or_contents: Union[object, List], filepath: Optional[str] = None, 
               output_dir: Optional[str] = None, **kwargs) -> str:
        """
        Abstract export method to be implemented by subclasses.
        
        Args:
            content_or_contents: Content to export
            filepath: Optional specific file path
            output_dir: Optional output directory
            **kwargs: Additional format-specific options
            
        Returns:
            Path to exported file
        """
        pass
    
    def validate_content(self, content) -> ValidationResult:
        """
        Validate content against schema requirements.
        
        Args:
            content: Content to validate
            
        Returns:
            ValidationResult with validation status and errors
        """
        errors = []
        
        # Convert to dict if it's a dataclass
        if hasattr(content, '__dict__'):
            data = content.__dict__
        else:
            data = content
        
        # Check required fields
        for field in self.required_fields:
            if field not in data or not data[field]:
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Validate data types
        if 'images' in data and not isinstance(data['images'], list):
            errors.append("Field 'images' must be a list")
        
        if 'metadata' in data and not isinstance(data['metadata'], dict):
            errors.append("Field 'metadata' must be a dictionary")
        
        # Check content length if specified
        if 'content_html' in data:
            min_length = self.validation_config.get('min_content_length', 0)
            max_length = self.validation_config.get('max_content_length', float('inf'))
            content_length = len(data['content_html'])
            
            if content_length < min_length:
                errors.append(f"Content too short: {content_length} < {min_length} chars")
            elif content_length > max_length:
                errors.append(f"Content too long: {content_length} > {max_length} chars")
        
        return ValidationResult(len(errors) == 0, errors)
    
    def ensure_output_directory(self, output_dir: Optional[str] = None) -> Path:
        """
        Ensure output directory exists and return Path object.
        
        Args:
            output_dir: Optional output directory
            
        Returns:
            Path object for output directory
        """
        output_dir = output_dir or self.default_output_dir
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path
    
    def prepare_data(self, content, include_metadata: Optional[bool] = None) -> Dict[str, Any]:
        """
        Prepare content data for export.
        
        Args:
            content: Content to prepare
            include_metadata: Whether to include metadata
            
        Returns:
            Prepared data dictionary
        """
        # Convert to dict if needed
        if hasattr(content, '__dict__'):
            data = content.__dict__.copy()
        else:
            data = content.copy()
        
        # Handle metadata inclusion
        include_metadata = include_metadata if include_metadata is not None else self.include_metadata
        if not include_metadata and 'metadata' in data:
            # Keep essential metadata but remove internal details
            essential_metadata = {
                'scraped_at': data.get('scraped_at'),
                'source_url': data.get('source_url'),
            }
            data['metadata'] = {k: v for k, v in essential_metadata.items() if v}
        
        return data
    
    def generate_filename(self, content, extension: str, timestamp: bool = False) -> str:
        """
        Generate filename for content.
        
        Args:
            content: Content to generate filename for
            extension: File extension (without dot)
            timestamp: Whether to include timestamp
            
        Returns:
            Generated filename
        """
        if hasattr(content, '__dict__'):
            data = content.__dict__
        else:
            data = content
        
        base_name = data.get('slug', 'scraped_content')
        
        if timestamp:
            timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            return f"{base_name}_{timestamp_str}.{extension}"
        else:
            return f"{base_name}.{extension}"