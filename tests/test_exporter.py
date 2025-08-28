"""
Unit tests for exporter.py module.
Tests the ContentExporter class and export functionality.
"""

import pytest
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch, MagicMock

from exporter import ContentExporter, save_to_json
from exporters import ValidationResult, ExporterFactory
from exceptions import ValidationException


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_validation_result_valid(self):
        """Test ValidationResult for valid content."""
        result = ValidationResult(is_valid=True, errors=[])
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert bool(result) is True  # Should be truthy
    
    def test_validation_result_invalid(self):
        """Test ValidationResult for invalid content."""
        errors = ["Missing title", "Content too short"]
        result = ValidationResult(is_valid=False, errors=errors)
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert bool(result) is False  # Should be falsy
        assert "Missing title" in result.errors


class TestContentExporter:
    """Test ContentExporter class."""
    
    def test_exporter_initialization(self, test_config):
        """Test ContentExporter initialization."""
        exporter = ContentExporter(test_config)
        
        assert exporter.config == test_config
        assert exporter.output_config == test_config['output']
        # validation_config no longer exists - validation handled by individual exporters
        assert exporter.default_format == test_config['output'].get('format', 'json')
        assert 'json' in exporter.handlers
        assert 'csv' in exporter.handlers
        assert 'xml' in exporter.handlers
        assert 'wordpress_xml' in exporter.handlers
    
    def test_exporter_validate_output_success(self, test_config, sample_scraped_content):
        """Test successful content validation."""
        exporter = ContentExporter(test_config)
        
        result = exporter.validate_output(sample_scraped_content)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_exporter_validate_output_missing_title(self, test_config, sample_scraped_content):
        """Test validation with missing title."""
        exporter = ContentExporter(test_config)
        sample_scraped_content.title = ""  # Empty title
        
        result = exporter.validate_output(sample_scraped_content)
        
        assert result.is_valid is False
        assert "Required field 'title' is missing or empty" in result.errors
    
    def test_exporter_validate_output_missing_content(self, test_config, sample_scraped_content):
        """Test validation with missing content."""
        exporter = ContentExporter(test_config)
        sample_scraped_content.content_html = ""  # Empty content
        
        result = exporter.validate_output(sample_scraped_content)
        
        assert result.is_valid is False
        assert "Required field 'content_html' is missing or empty" in result.errors
    
    def test_exporter_validate_output_content_too_short(self, test_config, sample_scraped_content):
        """Test validation with content too short."""
        test_config['validation']['min_content_length'] = 100
        exporter = ContentExporter(test_config)
        sample_scraped_content.content_html = "<p>Short</p>"  # Only ~11 chars
        
        result = exporter.validate_output(sample_scraped_content)
        
        assert result.is_valid is False
        assert "Content too short" in result.errors[0]
    
    def test_exporter_validate_output_content_too_long(self, test_config, sample_scraped_content):
        """Test validation with content too long."""
        test_config['validation']['min_content_length'] = 10  # Set low min
        test_config['validation']['max_content_length'] = 20   # Set low max
        exporter = ContentExporter(test_config)
        sample_scraped_content.content_html = "<p>" + "x" * 50 + "</p>"  # Much longer
        
        result = exporter.validate_output(sample_scraped_content)
        
        assert result.is_valid is False
        assert "Content too long" in result.errors[0]


class TestJSONExport:
    """Test JSON export functionality."""
    
    def test_export_json_single_item(self, test_config, sample_scraped_content, temp_dir):
        """Test JSON export of single item."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        filepath = exporter.export_json(sample_scraped_content, str(output_file))
        
        assert Path(filepath).exists()
        assert filepath.endswith('.json')
        
        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert data['title'] == "Test Title"
        assert data['source_url'] == "https://example.com/test"
        assert len(data['images']) == 1
    
    def test_export_json_list_items(self, test_config, sample_scraped_content, temp_dir):
        """Test JSON export of list of items."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Create list of content
        content_list = [sample_scraped_content, sample_scraped_content]
        
        filepath = exporter.export_json(content_list, str(output_file))
        
        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data, list)
        assert len(data) == 2
        assert all(item['title'] == "Test Title" for item in data)
    
    def test_export_json_auto_filename(self, test_config, sample_scraped_content, temp_dir):
        """Test JSON export with automatic filename generation."""
        exporter = ContentExporter(test_config)
        
        # Change to temp directory for test
        with patch('pathlib.Path.cwd', return_value=temp_dir):
            filepath = exporter.export_json(sample_scraped_content)
        
        assert Path(filepath).exists()
        assert "test-title" in filepath  # Should use slug for filename
    
    def test_export_json_validation_failure(self, test_config, sample_scraped_content):
        """Test JSON export with validation failure."""
        exporter = ContentExporter(test_config)
        sample_scraped_content.title = ""  # Make invalid
        
        with pytest.raises(ValidationException) as exc_info:
            exporter.export_json(sample_scraped_content, "test_output")
        
        assert "Content validation failed" in str(exc_info.value)
    
    def test_export_json_pretty_print(self, test_config, sample_scraped_content, temp_dir):
        """Test JSON export with pretty printing."""
        test_config['output']['pretty_print'] = True
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        filepath = exporter.export_json(sample_scraped_content, str(output_file))
        
        # Read raw content to check formatting
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Pretty printed JSON should have indentation
        assert '  "title"' in content or '    "title"' in content


class TestCSVExport:
    """Test CSV export functionality."""
    
    def test_export_csv_single_item(self, test_config, sample_scraped_content, temp_dir):
        """Test CSV export of single item."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        filepath = exporter.export_csv([sample_scraped_content], str(output_file))
        
        assert Path(filepath).exists()
        assert filepath.endswith('.csv')
        
        # Verify content
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['title'] == "Test Title"
        assert rows[0]['source_url'] == "https://example.com/test"
    
    def test_export_csv_multiple_items(self, test_config, sample_scraped_content, temp_dir):
        """Test CSV export of multiple items."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Create multiple items with different data
        content1 = sample_scraped_content
        content2 = sample_scraped_content.__class__(
            title="Second Title",
            slug="second-title",
            source_url="https://example.com/second",
            content_html="<h2>Second</h2>",
            images=[],
            scraped_at="2025-08-27T01:00:00Z"
        )
        
        filepath = exporter.export_csv([content1, content2], str(output_file))
        
        # Verify content
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['title'] == "Test Title"
        assert rows[1]['title'] == "Second Title"
    
    def test_export_csv_auto_filename(self, test_config, sample_scraped_content, temp_dir):
        """Test CSV export with automatic filename generation."""
        exporter = ContentExporter(test_config)
        
        with patch('pathlib.Path.cwd', return_value=temp_dir):
            filepath = exporter.export_csv([sample_scraped_content])
        
        assert Path(filepath).exists()
        assert filepath.endswith('.csv')
        assert "scraped_content_" in filepath  # Should have timestamp
    
    def test_export_csv_validation_failure(self, test_config, sample_scraped_content):
        """Test CSV export with validation failure."""
        exporter = ContentExporter(test_config)
        sample_scraped_content.title = ""  # Make invalid
        
        with pytest.raises(ValidationException) as exc_info:
            exporter.export_csv([sample_scraped_content], "test_output")
        
        assert "Content validation failed" in str(exc_info.value)
    
    def test_export_csv_metadata_flattening(self, test_config, sample_scraped_content, temp_dir):
        """Test CSV export with metadata flattening."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Add complex metadata
        sample_scraped_content.metadata = {
            'scrape_duration': 1.5,
            'nested': {'key': 'value'},
            'list': [1, 2, 3]
        }
        
        filepath = exporter.export_csv([sample_scraped_content], str(output_file))
        
        # Verify metadata is flattened
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert 'metadata_scrape_duration' in reader.fieldnames
        assert rows[0]['metadata_scrape_duration'] == '1.5'


class TestXMLExport:
    """Test XML export functionality."""
    
    def test_export_xml_single_item(self, test_config, sample_scraped_content, temp_dir):
        """Test XML export of single item."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        filepath = exporter.export_xml([sample_scraped_content], str(output_file))
        
        assert Path(filepath).exists()
        assert filepath.endswith('.xml')
        
        # Verify content
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        assert root.tag == "scraped_contents"
        assert len(root.findall("item")) == 1
        
        item = root.find("item")
        assert item.find("title").text == "Test Title"
        assert item.find("source_url").text == "https://example.com/test"
    
    def test_export_xml_multiple_items(self, test_config, sample_scraped_content, temp_dir):
        """Test XML export of multiple items."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Create multiple items
        content_list = [sample_scraped_content, sample_scraped_content]
        
        filepath = exporter.export_xml(content_list, str(output_file))
        
        # Verify content
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        assert len(root.findall("item")) == 2
        assert root.get("count") == "2"
    
    def test_export_xml_auto_filename(self, test_config, sample_scraped_content, temp_dir):
        """Test XML export with automatic filename generation."""
        exporter = ContentExporter(test_config)
        
        with patch('pathlib.Path.cwd', return_value=temp_dir):
            filepath = exporter.export_xml([sample_scraped_content])
        
        assert Path(filepath).exists()
        assert filepath.endswith('.xml')
        assert "scraped_content_" in filepath
    
    def test_export_xml_validation_failure(self, test_config, sample_scraped_content):
        """Test XML export with validation failure."""
        exporter = ContentExporter(test_config)
        sample_scraped_content.title = ""  # Make invalid
        
        with pytest.raises(ValidationException) as exc_info:
            exporter.export_xml([sample_scraped_content], "test_output")
        
        assert "Content validation failed" in str(exc_info.value)
    
    def test_export_xml_special_characters(self, test_config, sample_scraped_content, temp_dir):
        """Test XML export with special characters."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Add content with special characters
        sample_scraped_content.content_html = "<p>Content with & < > \" ' characters</p>"
        
        filepath = exporter.export_xml([sample_scraped_content], str(output_file))
        
        # Verify content is properly escaped
        tree = ET.parse(filepath)
        item = tree.getroot().find("item")
        content = item.find("content_html").text
        
        assert "&" in content
        assert "<p>" in content  # HTML should be preserved


class TestModuleFunctions:
    """Test module-level convenience functions."""
    
    def test_save_to_json_function(self, temp_dir):
        """Test save_to_json convenience function."""
        output_dir = str(temp_dir)
        
        filepath = save_to_json(
            slug="test-slug",
            url="https://example.com",
            html="<p>Test content</p>",
            images=["https://example.com/image.jpg"],
            output_dir=output_dir
        )
        
        assert Path(filepath).exists()
        assert filepath.endswith('.json')
        
        # Verify content
        with open(filepath, 'r') as f:
            data = json.load(f)
        assert data['slug'] == "test-slug"
        assert data['source_url'] == "https://example.com"


class TestErrorHandling:
    """Test error handling in export functions."""
    
    def test_export_json_file_permission_error(self, test_config, sample_scraped_content):
        """Test JSON export with file permission error."""
        exporter = ContentExporter(test_config)
        
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(Exception):  # Should propagate the permission error
                exporter.export_json(sample_scraped_content, "/invalid/path/test")
    
    def test_export_csv_encoding_handling(self, test_config, sample_scraped_content, temp_dir):
        """Test CSV export with Unicode content."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Add Unicode content
        sample_scraped_content.title = "Café & Naïve Test 中文"
        sample_scraped_content.content_html = "<p>Unicode content: ñáéíóú 中文测试</p>"
        
        filepath = exporter.export_csv([sample_scraped_content], str(output_file))
        
        # Should handle Unicode without errors
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Café" in content
            assert "中文" in content
    
    def test_export_xml_invalid_characters(self, test_config, sample_scraped_content, temp_dir):
        """Test XML export with invalid XML characters."""
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        # Add content with control characters (invalid in XML)
        sample_scraped_content.content_html = "<p>Content with \\x00 control chars \\x01</p>"
        
        # Should handle gracefully (either remove or escape)
        filepath = exporter.export_xml([sample_scraped_content], str(output_file))
        
        # Should produce valid XML
        tree = ET.parse(filepath)  # This will raise if XML is invalid
        assert tree is not None


class TestConfigurationOptions:
    """Test configuration-driven behavior."""
    
    def test_exporter_with_metadata_disabled(self, test_config, sample_scraped_content, temp_dir):
        """Test export with metadata disabled."""
        test_config['output']['include_metadata'] = False
        exporter = ContentExporter(test_config)
        output_file = temp_dir / "test_output"
        
        filepath = exporter.export_json(sample_scraped_content, str(output_file))
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Metadata should not be included
        assert 'metadata' not in data
    
    def test_exporter_custom_validation_rules(self, test_config, sample_scraped_content):
        """Test exporter with custom validation rules."""
        # Set stricter validation
        test_config['validation']['min_content_length'] = 1000
        test_config['validation']['required_fields'] = ['title', 'content_html', 'custom_field']
        
        exporter = ContentExporter(test_config)
        
        result = exporter.validate_output(sample_scraped_content)
        
        assert result.is_valid is False
        assert any("below minimum" in error for error in result.errors)
        assert any("'custom_field'" in error for error in result.errors)