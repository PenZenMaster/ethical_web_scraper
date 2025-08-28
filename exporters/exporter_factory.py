"""
Module/Script Name: exporter_factory.py
Path: ethical_web_scraper/exporters/exporter_factory.py

Description:
Factory pattern implementation for creating exporter instances.
Provides centralized exporter creation with proper configuration injection.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Factory pattern for modular exporter system
"""

from typing import Dict, Any
import logging

from .base_exporter import BaseExporter
from .json_exporter import JSONExporter
from .csv_exporter import CSVExporter
from .xml_exporter import XMLExporter
from .wordpress_exporter import WordPressExporter
from exceptions import ValidationException


class ExporterFactory:
    """Factory for creating exporter instances based on format type."""
    
    # Registry of available exporters
    _exporters = {
        'json': JSONExporter,
        'csv': CSVExporter,
        'xml': XMLExporter,
        'wordpress_xml': WordPressExporter,
        'wordpress': WordPressExporter,  # Alias for convenience
    }
    
    @classmethod
    def create_exporter(cls, format_type: str, config: Dict[str, Any], logger: logging.Logger) -> BaseExporter:
        """
        Create an exporter instance for the specified format.
        
        Args:
            format_type: Export format type (json, csv, xml, wordpress_xml)
            config: Configuration dictionary
            logger: Logger instance
            
        Returns:
            BaseExporter: Configured exporter instance
            
        Raises:
            ValidationException: If format_type is not supported
        """
        format_type = format_type.lower().strip()
        
        if format_type not in cls._exporters:
            available_formats = ', '.join(cls._exporters.keys())
            raise ValidationException(
                f"Unsupported export format: '{format_type}'. Available formats: {available_formats}",
                validation_type="export_format"
            )
        
        exporter_class = cls._exporters[format_type]
        return exporter_class(config, logger)
    
    @classmethod
    def get_supported_formats(cls) -> list:
        """
        Get list of supported export formats.
        
        Returns:
            list: List of supported format strings
        """
        return list(cls._exporters.keys())
    
    @classmethod
    def register_exporter(cls, format_type: str, exporter_class: type) -> None:
        """
        Register a new exporter class for a format type.
        
        Args:
            format_type: Format identifier
            exporter_class: Exporter class that inherits from BaseExporter
            
        Raises:
            ValidationException: If exporter_class is not a BaseExporter subclass
        """
        if not issubclass(exporter_class, BaseExporter):
            raise ValidationException(
                f"Exporter class must inherit from BaseExporter",
                validation_type="exporter_registration"
            )
        
        cls._exporters[format_type.lower()] = exporter_class