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
        
        elif format_type.lower() == 'wordpress_xml':
            # WordPress XML export expects list of contents
            contents = content_or_contents if isinstance(content_or_contents, list) else [content_or_contents]
            return self.export_wordpress_xml(contents, filepath, output_dir)
        
        else:
            exc = ValidationException(
                f"Unsupported export format: {format_type}. Supported: json, csv, xml, wordpress_xml",
                validation_type="export_format"
            )
            handle_exception(exc, self.logger)

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
        if not contents:
            raise ValidationException("No content provided for WordPress XML export", validation_type="export_validation")
        
        # Create WordPress XML structure
        root = ET.Element("rss")
        root.set("version", "2.0")
        root.set("xmlns:excerpt", "http://wordpress.org/export/1.2/excerpt/")
        root.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
        root.set("xmlns:wfw", "http://wellformedweb.org/CommentAPI/")
        root.set("xmlns:dc", "http://purl.org/dc/elements/1.1/")
        root.set("xmlns:wp", "http://wordpress.org/export/1.2/")
        
        channel = ET.SubElement(root, "channel")
        
        # Channel metadata
        ET.SubElement(channel, "title").text = "WordPress Migration Export"
        ET.SubElement(channel, "link").text = "https://yoursite.com"
        ET.SubElement(channel, "description").text = "Exported content from ethical web scraper"
        ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
        ET.SubElement(channel, "language").text = "en-US"
        ET.SubElement(channel, "wp:wxr_version").text = "1.2"
        ET.SubElement(channel, "wp:base_site_url").text = "https://yoursite.com"
        ET.SubElement(channel, "wp:base_blog_url").text = "https://yoursite.com"
        
        # Add site info
        ET.SubElement(channel, "generator").text = "Ethical Web Scraper WordPress Migration Tool"
        
        # WordPress config from config file
        wp_config = self.config.get('wordpress_settings', {})
        post_status = wp_config.get('post_status', 'draft')
        post_type = wp_config.get('post_type', 'post')
        author_id = wp_config.get('author_id', 1)
        
        # Process each content item
        for i, content in enumerate(contents):
            if hasattr(content, '__dict__'):
                data = content.__dict__
            else:
                data = content
                
            # Create item (WordPress post)
            item = ET.SubElement(channel, "item")
            
            # Basic post data
            title = data.get('title', f'Imported Post {i+1}')
            ET.SubElement(item, "title").text = title
            ET.SubElement(item, "link").text = data.get('source_url', '')
            ET.SubElement(item, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
            ET.SubElement(item, "dc:creator").text = f"user{author_id}"
            ET.SubElement(item, "guid", isPermaLink="false").text = f"import-{i+1}-{datetime.utcnow().timestamp()}"
            ET.SubElement(item, "description").text = ""
            
            # Content
            content_html = data.get('content_html', '')
            if content_html:
                content_elem = ET.SubElement(item, "content:encoded")
                # Use direct text assignment without CDATA wrapper to avoid double-encoding
                content_elem.text = content_html
            
            # WordPress specific fields
            ET.SubElement(item, "wp:post_id").text = str(1000 + i)  # Start from 1000
            ET.SubElement(item, "wp:post_date").text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            ET.SubElement(item, "wp:post_date_gmt").text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            ET.SubElement(item, "wp:comment_status").text = "closed"
            ET.SubElement(item, "wp:ping_status").text = "closed"
            ET.SubElement(item, "wp:post_name").text = data.get('slug', f'imported-post-{i+1}')
            ET.SubElement(item, "wp:status").text = post_status
            ET.SubElement(item, "wp:post_parent").text = "0"
            ET.SubElement(item, "wp:menu_order").text = "0"
            ET.SubElement(item, "wp:post_type").text = post_type
            ET.SubElement(item, "wp:post_password").text = ""
            ET.SubElement(item, "wp:is_sticky").text = "0"
            
            # Add custom fields for metadata
            if 'metadata' in data:
                for key, value in data['metadata'].items():
                    if key not in ['title', 'url']:  # Skip duplicated fields
                        meta = ET.SubElement(item, "wp:postmeta")
                        ET.SubElement(meta, "wp:meta_key").text = f"_scraped_{key}"
                        ET.SubElement(meta, "wp:meta_value").text = str(value)
            
            # Add source URL as custom field
            if 'source_url' in data:
                meta = ET.SubElement(item, "wp:postmeta")
                ET.SubElement(meta, "wp:meta_key").text = "_scraped_source_url"
                ET.SubElement(meta, "wp:meta_value").text = data['source_url']
        
        # Generate filepath
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"wordpress_import_{timestamp}"
            
            if output_dir:
                output_path = Path(output_dir)
            else:
                output_path = Path(self.config.get('output', {}).get('directory', 'output'))
            
            output_path.mkdir(exist_ok=True)
            filepath = output_path / f"{base_name}.xml"
        else:
            filepath = Path(filepath)
            if filepath.suffix != '.xml':
                filepath = filepath.with_suffix('.xml')
        
        # Write XML with proper formatting
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        
        try:
            with open(filepath, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                tree.write(f, encoding='utf-8', xml_declaration=False)
            
            self.logger.info(f"WordPress XML exported to: {filepath} ({len(contents)} posts)")
            return str(filepath)
            
        except Exception as e:
            exc = ValidationException(f"Failed to write WordPress XML: {e}", validation_type="file_write")
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