"""
Module/Script Name: exporter.py
Path: ethical_web_scraper/exporter.py

Description:
Content export module for the Ethical Web Scraper project supporting JSON, CSV,
XML, and WordPress XML output formats. Refactored to use modular export components
for better separation of concerns.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Refactored to use modular export components
* v1.00 - Initial implementation with JSON export and validation
"""

import logging
from typing import Dict, Any, List, Optional, Union

from exporters import (
    ValidationResult, 
    JSONExporter,
    CSVExporter,
    XMLExporter,
    WordPressExporter
)
from exceptions import ValidationException, handle_exception


class ContentExporter:
    """
    Handles export of scraped content to various formats with validation.
    Coordinates different export format handlers.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize content exporter.
        
        Args:
            config: Configuration dictionary with output settings
        """
        self.config = config or {}
        self.output_config = self.config.get('output', {})
        self.logger = logging.getLogger('ethical_web_scraper.exporter')
        
        # Output settings
        self.default_format = self.output_config.get('format', 'json')
        
        # Initialize format handlers
        self.handlers = {
            'json': JSONExporter(self.config, self.logger),
            'csv': CSVExporter(self.config, self.logger),
            'xml': XMLExporter(self.config, self.logger),
            'wordpress_xml': WordPressExporter(self.config, self.logger)
        }
        
        self.logger.debug(f"ContentExporter initialized - Format: {self.default_format}")

    def validate_output(self, content) -> ValidationResult:
        """
        Validate scraped content against schema requirements.
        
        Args:
            content: ScrapedContent instance or dictionary
            
        Returns:
            ValidationResult with validation status and errors
        """
        # Use JSON exporter's validation as it's the most comprehensive
        return self.handlers['json'].validate_content(content)

    def export_json(
        self, 
        content, 
        filepath: Optional[str] = None,
        output_dir: Optional[str] = None,
        pretty: Optional[bool] = None
    ) -> str:
        """
        Export content to JSON format.
        
        Args:
            content: ScrapedContent instance or dictionary
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            pretty: Pretty print JSON (defaults to config)
            
        Returns:
            Path to exported file
            
        Raises:
            ValidationException: If content validation fails
        """
        return self.handlers['json'].export(content, filepath, output_dir, pretty=pretty)

    def export_csv(
        self, 
        contents: List, 
        filepath: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Export multiple contents to CSV format.
        
        Args:
            contents: List of ScrapedContent instances or dictionaries
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            
        Returns:
            Path to exported file
        """
        return self.handlers['csv'].export(contents, filepath, output_dir)

    def export_xml(
        self, 
        contents: List, 
        filepath: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Export contents to XML format.
        
        Args:
            contents: List of ScrapedContent instances or dictionaries
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            
        Returns:
            Path to exported file
        """
        return self.handlers['xml'].export(contents, filepath, output_dir)

    def export_wordpress_xml(
        self,
        contents: List,
        filepath: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Export contents to WordPress XML format for import via WordPress admin.
        
        Args:
            contents: List of ScrapedContent instances or dictionaries
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            
        Returns:
            Path to exported file
        """
        return self.handlers['wordpress_xml'].export(contents, filepath, output_dir)

    def export(
        self, 
        content_or_contents: Union[object, List], 
        format_type: Optional[str] = None,
        filepath: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Export content in specified format.
        
        Args:
            content_or_contents: Single content or list of contents
            format_type: Export format ('json', 'csv', 'xml', 'wordpress_xml')
            filepath: Specific file path
            output_dir: Output directory
            
        Returns:
            Path to exported file
        """
        format_type = format_type or self.default_format
        
        # Get the appropriate handler
        handler = self.handlers.get(format_type.lower())
        if not handler:
            exc = ValidationException(
                f"Unsupported export format: {format_type}. Supported: {', '.join(self.handlers.keys())}",
                validation_type="export_format"
            )
            handle_exception(exc, self.logger)
        
        # Handle format-specific requirements
        if format_type.lower() == 'json':
            # JSON export expects single content
            if isinstance(content_or_contents, list):
                if len(content_or_contents) == 1:
                    return handler.export(content_or_contents[0], filepath, output_dir)
                else:
                    exc = ValidationException(
                        "JSON export requires single content item. Use CSV or XML for multiple items.",
                        validation_type="export_format"
                    )
                    handle_exception(exc, self.logger)
            else:
                return handler.export(content_or_contents, filepath, output_dir)
        else:
            # Other formats can handle both single items and lists
            return handler.export(content_or_contents, filepath, output_dir)


# Convenience functions for backward compatibility
def save_to_json(slug: str, url: str, html: str, images: List[str], output_dir: str = "output") -> str:
    """
    Backward compatibility function for simple JSON export.
    
    Args:
        slug: Content slug
        url: Source URL
        html: HTML content
        images: List of image URLs
        output_dir: Output directory
        
    Returns:
        Path to exported file
    """
    from utils import get_timestamp
    
    data = {
        "title": slug.replace("-", " ").title(),
        "slug": slug,
        "source_url": url,
        "content_html": html,
        "images": images,
        "scraped_at": get_timestamp()
    }
    
    exporter = ContentExporter()
    return exporter.export_json(data, output_dir=output_dir)


# Re-export ValidationResult for backward compatibility
__all__ = ['ContentExporter', 'ValidationResult', 'save_to_json']