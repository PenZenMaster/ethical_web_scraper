"""
Module/Script Name: wordpress_exporter.py
Path: ethical_web_scraper/exporters/wordpress_exporter.py

Description:
WordPress XML export functionality extracted from exporter.py for better modularity.
Handles WordPress-specific XML format for direct import into WordPress.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ContentExporter.export_wordpress_xml method
"""

import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_exporter import BaseExporter
from exceptions import ValidationException, handle_exception


class WordPressExporter(BaseExporter):
    """Handles WordPress XML format export for direct import."""
    
    def export(self, content_or_contents: Union[object, List], filepath: Optional[str] = None, 
               output_dir: Optional[str] = None) -> str:
        """
        Export contents to WordPress XML format for import via WordPress admin.
        
        Args:
            content_or_contents: Content(s) to export
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            
        Returns:
            Path to exported file
        """
        # WordPress export expects list of contents
        contents = content_or_contents if isinstance(content_or_contents, list) else [content_or_contents]
        
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
            data = self.prepare_data(content)
            
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
                output_path = self.ensure_output_directory()
            
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