"""
Module/Script Name: xml_exporter.py
Path: ethical_web_scraper/exporters/xml_exporter.py

Description:
XML export functionality extracted from exporter.py for better modularity.
Handles XML format export with proper structure and formatting.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ContentExporter.export_xml method
"""

import xml.etree.ElementTree as ET
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_exporter import BaseExporter
from exceptions import ValidationException, handle_exception


class XMLExporter(BaseExporter):
    """Handles XML format export with proper structure."""
    
    def export(self, content_or_contents: Union[object, List], filepath: Optional[str] = None, 
               output_dir: Optional[str] = None) -> str:
        """
        Export contents to XML format.
        
        Args:
            content_or_contents: Content(s) to export
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            
        Returns:
            Path to exported file
        """
        # XML export expects list of contents
        contents = content_or_contents if isinstance(content_or_contents, list) else [content_or_contents]
        
        if not contents:
            raise ValidationException("No content provided for XML export", validation_type="export_validation")
        
        # Create XML structure
        root = ET.Element("scraped_contents")
        root.set("exported_at", datetime.utcnow().isoformat() + 'Z')
        root.set("count", str(len(contents)))
        
        for content in contents:
            # Validate content first
            validation_result = self.validate_content(content)
            if not validation_result:
                exc = ValidationException(
                    f"Content validation failed: {', '.join(validation_result.errors)}",
                    validation_type="export_validation"
                )
                handle_exception(exc, self.logger)
            
            data = self.prepare_data(content)
            
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
            # Ensure .xml extension for backward compatibility
            if output_path.suffix != '.xml':
                output_path = output_path.with_suffix('.xml')
        else:
            output_dir_path = self.ensure_output_directory(output_dir)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_content_{timestamp}.xml"
            output_path = output_dir_path / filename
        
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