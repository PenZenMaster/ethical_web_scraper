"""
Module/Script Name: csv_exporter.py
Path: ethical_web_scraper/exporters/csv_exporter.py

Description:
CSV export functionality extracted from exporter.py for better modularity.
Handles CSV format export with field flattening for multiple records.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-28

Last Modified Date:
2025-08-28

Comments:
* v1.1 - Extracted from ContentExporter.export_csv method
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_exporter import BaseExporter
from exceptions import ValidationException, handle_exception


class CSVExporter(BaseExporter):
    """Handles CSV format export with field flattening."""
    
    def export(self, content_or_contents: Union[object, List], filepath: Optional[str] = None, 
               output_dir: Optional[str] = None) -> str:
        """
        Export multiple contents to CSV format.
        
        Args:
            content_or_contents: Content(s) to export
            filepath: Specific file path (overrides auto-generation)
            output_dir: Output directory (defaults to config)
            
        Returns:
            Path to exported file
        """
        # CSV export expects list of contents
        contents = content_or_contents if isinstance(content_or_contents, list) else [content_or_contents]
        
        if not contents:
            raise ValidationException("No content provided for CSV export", validation_type="export_validation")
        
        # Convert all content to dicts and flatten complex fields
        data_list = []
        for content in contents:
            data = self.prepare_data(content)
            
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
            output_dir_path = self.ensure_output_directory(output_dir)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"scraped_content_{timestamp}.csv"
            output_path = output_dir_path / filename
        
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