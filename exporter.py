"""
Module/Script Name: exporter.py
Path: ethical_web_scraper/exporter.py

Description:
Content export module for the Ethical Web Scraper project supporting JSON, CSV,
and XML output formats with schema validation.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-27

Comments:
* v1.00 - Initial implementation with JSON export and validation
"""

import json
import csv
import xml.etree.ElementTree as ET
import logging
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


class ContentExporter:
    """
    Handles export of scraped content to various formats with validation.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize content exporter.
        
        Args:
            config: Configuration dictionary with output settings
        """
        self.config = config or {}
        self.output_config = self.config.get('output', {})
        self.validation_config = self.config.get('validation', {})
        self.logger = logging.getLogger('ethical_web_scraper.exporter')
        
        # Output settings
        self.default_format = self.output_config.get('format', 'json')
        self.pretty_print = self.output_config.get('pretty_print', True)
        self.include_metadata = self.output_config.get('include_metadata', True)
        self.default_output_dir = self.output_config.get('directory', 'output')
        
        # Validation settings
        self.required_fields = self.validation_config.get('required_fields', ['title', 'content_html'])
        
        self.logger.debug(f"ContentExporter initialized - Format: {self.default_format}")

    def validate_output(self, content) -> ValidationResult:
        """
        Validate scraped content against schema requirements.
        
        Args:
            content: ScrapedContent instance or dictionary
            
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
        # Validate content
        validation_result = self.validate_output(content)
        if not validation_result:
            exc = ValidationException(
                f"Content validation failed: {', '.join(validation_result.errors)}",
                validation_type="export_validation"
            )
            handle_exception(exc, self.logger)
        
        # Convert to dict if needed
        if hasattr(content, '__dict__'):
            data = content.__dict__.copy()
        else:
            data = content.copy()
        
        # Remove internal fields if not including metadata
        if not self.include_metadata and 'metadata' in data:
            # Keep essential metadata but remove internal details
            essential_metadata = {
                'scraped_at': data.get('scraped_at'),
                'source_url': data.get('source_url'),
            }
            data['metadata'] = {k: v for k, v in essential_metadata.items() if v}
        
        # Determine output path
        if filepath:
            output_path = Path(filepath)
        else:
            output_dir = output_dir or self.default_output_dir
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            filename = f"{data.get('slug', 'scraped_content')}.json"
            output_path = Path(output_dir) / filename
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export JSON
        pretty_print = pretty if pretty is not None else self.pretty_print
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            self.logger.info(f"JSON exported to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            exc = ValidationException(f"Failed to export JSON: {e}", validation_type="file_export")
            handle_exception(exc, self.logger)

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
        if not contents:
            raise ValidationException("No content provided for CSV export", validation_type="export_validation")
        
        # Convert all content to dicts
        data_list = []
        for content in contents:
            if hasattr(content, '__dict__'):
                data = content.__dict__.copy()
            else:
                data = content.copy()
            
            # Flatten complex fields for CSV
            data['images'] = ', '.join(data.get('images', []))
            if 'metadata' in data and isinstance(data['metadata'], dict):
                # Add key metadata fields as columns
                for key, value in data['metadata'].items():
                    if isinstance(value, (str, int, float, bool)):
                        data[f'metadata_{key}'] = value
                del data['metadata']
            
            data_list.append(data)
        
        # Determine output path
        if filepath:
            output_path = Path(filepath)
        else:
            output_dir = output_dir or self.default_output_dir
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_content_{timestamp}.csv"
            output_path = Path(output_dir) / filename
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export CSV
        try:
            fieldnames = set()
            for data in data_list:
                fieldnames.update(data.keys())
            fieldnames = sorted(fieldnames)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data_list)
            
            self.logger.info(f"CSV exported to: {output_path} ({len(data_list)} records)")
            return str(output_path)
            
        except Exception as e:
            exc = ValidationException(f"Failed to export CSV: {e}", validation_type="file_export")
            handle_exception(exc, self.logger)

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
        if not contents:
            raise ValidationException("No content provided for XML export", validation_type="export_validation")
        
        # Create XML structure
        root = ET.Element("scraped_contents")
        root.set("exported_at", datetime.utcnow().isoformat() + 'Z')
        root.set("count", str(len(contents)))
        
        for content in contents:
            if hasattr(content, '__dict__'):
                data = content.__dict__
            else:
                data = content
            
            item = ET.SubElement(root, "item")
            
            for key, value in data.items():
                elem = ET.SubElement(item, key)
                if isinstance(value, list):
                    for item_value in value:
                        sub_elem = ET.SubElement(elem, "item")
                        sub_elem.text = str(item_value)
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        sub_elem = ET.SubElement(elem, sub_key)
                        sub_elem.text = str(sub_value)
                else:
                    elem.text = str(value) if value is not None else ""
        
        # Determine output path
        if filepath:
            output_path = Path(filepath)
        else:
            output_dir = output_dir or self.default_output_dir
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_content_{timestamp}.xml"
            output_path = Path(output_dir) / filename
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Export XML
        try:
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            tree.write(output_path, encoding='utf-8', xml_declaration=True)
            
            self.logger.info(f"XML exported to: {output_path} ({len(contents)} records)")
            return str(output_path)
            
        except Exception as e:
            exc = ValidationException(f"Failed to export XML: {e}", validation_type="file_export")
            handle_exception(exc, self.logger)

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
            format_type: Export format ('json', 'csv', 'xml')
            filepath: Specific file path
            output_dir: Output directory
            
        Returns:
            Path to exported file
        """
        format_type = format_type or self.default_format
        
        if format_type.lower() == 'json':
            # JSON export expects single content
            if isinstance(content_or_contents, list):
                if len(content_or_contents) == 1:
                    return self.export_json(content_or_contents[0], filepath, output_dir)
                else:
                    raise ValidationException(
                        "JSON export requires single content item. Use CSV or XML for multiple items.",
                        validation_type="export_format"
                    )
            else:
                return self.export_json(content_or_contents, filepath, output_dir)
        
        elif format_type.lower() == 'csv':
            # CSV export expects list of contents
            contents = content_or_contents if isinstance(content_or_contents, list) else [content_or_contents]
            return self.export_csv(contents, filepath, output_dir)
        
        elif format_type.lower() == 'xml':
            # XML export expects list of contents
            contents = content_or_contents if isinstance(content_or_contents, list) else [content_or_contents]
            return self.export_xml(contents, filepath, output_dir)
        
        else:
            exc = ValidationException(
                f"Unsupported export format: {format_type}. Supported: json, csv, xml",
                validation_type="export_format"
            )
            handle_exception(exc, self.logger)


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