"""
Module/Script Name: json_exporter.py
Path: ethical_web_scraper/exporters/json_exporter.py

Description:
JSON export functionality extracted from exporter.py for better modularity.
Handles JSON format export with validation and pretty printing options.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ContentExporter.export_json method
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from .base_exporter import BaseExporter
from exceptions import ValidationException, handle_exception


class JSONExporter(BaseExporter):
    """Handles JSON format export with validation."""
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize JSON exporter.
        
        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        super().__init__(config, logger)
        self.pretty_print = self.output_config.get('pretty_print', True)
    
    def export(self, content_or_contents: Union[object, List], filepath: Optional[str] = None, 
               output_dir: Optional[str] = None, pretty: Optional[bool] = None) -> str:
        """
        Export content to JSON format.
        
        Args:
            content_or_contents: Content to export (expects single content for JSON)
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            pretty: Pretty print JSON (defaults to config)
            
        Returns:
            Path to exported file
            
        Raises:
            ValidationException: If content validation fails
        """
        # Handle both single content and lists for backward compatibility
        if isinstance(content_or_contents, list):
            if len(content_or_contents) == 1:
                # Single item in list - extract it
                content = content_or_contents[0]
                is_list_export = False
            else:
                # Multiple items - export as JSON array
                content = content_or_contents
                is_list_export = True
        else:
            content = content_or_contents
            is_list_export = False
        
        # Validate and prepare data
        if is_list_export:
            # Validate each item in the list
            for item in content:
                validation_result = self.validate_content(item)
                if not validation_result:
                    exc = ValidationException(
                        f"Content validation failed: {', '.join(validation_result.errors)}",
                        validation_type="export_validation"
                    )
                    handle_exception(exc, self.logger)
            
            # Prepare data for each item
            data = [self.prepare_data(item) for item in content]
        else:
            # Single item validation and preparation
            validation_result = self.validate_content(content)
            if not validation_result:
                exc = ValidationException(
                    f"Content validation failed: {', '.join(validation_result.errors)}",
                    validation_type="export_validation"
                )
                handle_exception(exc, self.logger)
            
            data = self.prepare_data(content)
        
        # Determine output path
        if filepath:
            output_path = Path(filepath)
            # Ensure .json extension for backward compatibility
            if output_path.suffix != '.json':
                output_path = output_path.with_suffix('.json')
        else:
            output_dir_path = self.ensure_output_directory(output_dir)
            if is_list_export:
                # For list exports, use first item for filename generation
                filename = self.generate_filename(content[0], 'json')
            else:
                filename = self.generate_filename(content, 'json')
            output_path = output_dir_path / filename
        
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