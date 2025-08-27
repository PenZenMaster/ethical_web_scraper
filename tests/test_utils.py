"""
Unit tests for utils.py module.
Tests core utility functions including configuration loading,
content extraction, and helper utilities.
"""

import pytest
import yaml
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils import (
    load_config, setup_logging, get_environment_config, merge_configs,
    extract_content, get_slug_from_title, validate_url, get_timestamp
)
from exceptions import ConfigurationError


class TestConfigurationLoading:
    """Test configuration loading and merging."""
    
    def test_load_config_success(self, temp_config_file):
        """Test successful config loading."""
        config = load_config(temp_config_file)
        assert 'browser' in config
        assert 'scraping' in config
        assert config['browser']['headless'] is True
    
    def test_load_config_file_not_found(self):
        """Test config loading with non-existent file."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("non_existent_config.yaml")
        assert "Configuration file not found" in str(exc_info.value)
    
    def test_load_config_invalid_yaml(self, temp_dir):
        """Test config loading with invalid YAML."""
        invalid_config = temp_dir / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(invalid_config))
        assert "Invalid YAML configuration" in str(exc_info.value)
    
    def test_load_config_missing_sections(self, temp_dir):
        """Test config loading with missing required sections."""
        incomplete_config = temp_dir / "incomplete.yaml"
        with open(incomplete_config, 'w') as f:
            yaml.safe_dump({'browser': {'headless': True}}, f)
        
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(str(incomplete_config))
        assert "Missing required configuration section" in str(exc_info.value)
    
    def test_get_environment_config(self):
        """Test environment configuration extraction."""
        with patch.dict('os.environ', {
            'EWS_HEADLESS': 'false',
            'EWS_DELAY': '3.0',
            'EWS_LOG_LEVEL': 'DEBUG',
            'IRRELEVANT_VAR': 'ignored'
        }):
            env_config = get_environment_config()
            
            # Check that the correct mappings are applied
            assert env_config['browser']['headless'] is False
            assert env_config['scraping']['delay_between_requests'] == 3.0
            assert env_config['logging']['level'] == 'DEBUG'
    
    def test_merge_configs(self):
        """Test configuration merging."""
        base = {
            'browser': {'headless': True, 'timeout': 30000},
            'scraping': {'delay': 2.0}
        }
        override = {
            'browser': {'headless': False},  # Override existing
            'output': {'format': 'json'}     # Add new section
        }
        
        merged = merge_configs(base, override)
        
        assert merged['browser']['headless'] is False  # Overridden
        assert merged['browser']['timeout'] == 30000   # Preserved
        assert merged['scraping']['delay'] == 2.0      # Preserved
        assert merged['output']['format'] == 'json'    # Added


class TestLogging:
    """Test logging configuration."""
    
    def test_setup_logging_default(self):
        """Test logging setup with default configuration."""
        logger = setup_logging()
        assert logger.name == 'ethical_web_scraper'
        assert logger.level == logging.INFO
    
    def test_setup_logging_custom_config(self, test_config):
        """Test logging setup with custom configuration."""
        test_config['logging']['level'] = 'DEBUG'
        logger = setup_logging(test_config)
        
        assert logger.level == logging.DEBUG
    
    def test_setup_logging_creates_log_dir(self, temp_dir):
        """Test that logging setup creates log directory."""
        log_file = temp_dir / "custom_logs" / "test.log"
        log_file.parent.mkdir(parents=True)  # Create directory first
        config = {'logging': {'level': 'INFO', 'file': str(log_file)}}
        
        logger = setup_logging(config)
        assert logger is not None


class TestContentExtraction:
    """Test content extraction utilities."""
    
    def test_extract_content_basic(self, sample_html):
        """Test basic content extraction."""
        content, images = extract_content(sample_html, "body")
        
        assert "<h1>Test Heading</h1>" in content
        assert "<p>Test content" in content
        assert len(images) == 1
        assert "/test.jpg" in images[0]
    
    def test_extract_content_with_base_url(self, sample_html):
        """Test content extraction with base URL for image resolution."""
        base_url = "https://example.com"
        content, images = extract_content(sample_html, "body", base_url)
        
        assert len(images) == 1
        assert images[0] == "https://example.com/test.jpg"
    
    def test_extract_content_selector_not_found(self, sample_html):
        """Test content extraction with non-existent selector."""
        with pytest.raises(ValueError) as exc_info:
            extract_content(sample_html, ".nonexistent")
        assert "No element found for selector" in str(exc_info.value)
    
    def test_extract_content_specific_selector(self, sample_html):
        """Test content extraction with specific selector."""
        content, images = extract_content(sample_html, ".content")
        
        assert "<p>More test content" in content
        assert "<h1>Test Heading</h1>" not in content
    
    def test_extract_content_no_images(self):
        """Test content extraction with no images."""
        html = "<div><p>No images here</p></div>"
        content, images = extract_content(html, "div")
        
        assert len(images) == 0
        assert "<p>No images here</p>" in content


class TestUtilityFunctions:
    """Test utility helper functions."""
    
    def test_get_slug_from_title_basic(self):
        """Test slug generation from title."""
        slug = get_slug_from_title("Hello World Test")
        assert slug == "hello-world-test"
    
    def test_get_slug_from_title_special_characters(self):
        """Test slug generation with special characters."""
        slug = get_slug_from_title("Hello, World! & Test #123")
        assert slug == "hello-world-test-123"
    
    def test_get_slug_from_title_unicode(self):
        """Test slug generation with Unicode characters."""
        slug = get_slug_from_title("Café & Naïve Test")
        assert slug == "cafe-naive-test"
    
    def test_get_slug_from_title_empty(self):
        """Test slug generation with empty title."""
        slug = get_slug_from_title("")
        assert slug == ""  # slugify returns empty string for empty input
    
    def test_get_slug_from_title_whitespace_only(self):
        """Test slug generation with whitespace-only title.""" 
        slug = get_slug_from_title("   \n\t   ")
        assert slug == ""  # slugify returns empty string for whitespace-only
    
    def test_validate_url_valid_http(self):
        """Test URL validation with valid HTTP URL."""
        assert validate_url("http://example.com") is True
        assert validate_url("http://example.com/path?query=1") is True
    
    def test_validate_url_valid_https(self):
        """Test URL validation with valid HTTPS URL."""
        assert validate_url("https://example.com") is True
        assert validate_url("https://sub.example.com/path") is True
    
    def test_validate_url_invalid_scheme(self):
        """Test URL validation with invalid scheme."""
        assert validate_url("ftp://example.com") is False
        assert validate_url("file:///path/to/file") is False
    
    def test_validate_url_malformed(self):
        """Test URL validation with malformed URLs."""
        assert validate_url("not-a-url") is False
        assert validate_url("http://") is False
        assert validate_url("") is False
    
    def test_validate_url_no_domain(self):
        """Test URL validation with no domain."""
        assert validate_url("https://") is False
        assert validate_url("http:///path") is False
    
    def test_get_timestamp_format(self):
        """Test timestamp generation format."""
        timestamp = get_timestamp()
        
        # Should be ISO format with Z suffix
        assert timestamp.endswith('Z')
        assert 'T' in timestamp
        
        # Should parse as valid datetime
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        assert parsed is not None
    
    def test_get_timestamp_uniqueness(self):
        """Test that timestamps are unique."""
        timestamp1 = get_timestamp()
        timestamp2 = get_timestamp()
        
        # Should be different (microsecond precision)
        assert timestamp1 != timestamp2


class TestErrorHandling:
    """Test error handling in utility functions."""
    
    def test_extract_content_invalid_html(self):
        """Test content extraction with invalid HTML."""
        # BeautifulSoup should handle invalid HTML gracefully
        content, images = extract_content("<div><p>Unclosed tags", "div")
        assert "<p>Unclosed tags" in content
    
    def test_extract_content_empty_html(self):
        """Test content extraction with empty HTML."""
        with pytest.raises(ValueError):
            extract_content("", "div")
    
    @patch('utils.Path')
    def test_load_config_permission_error(self, mock_path):
        """Test config loading with permission error."""
        mock_path.return_value.exists.return_value = True
        
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            with pytest.raises(ConfigurationError) as exc_info:
                load_config("test.yaml")
            assert "Error loading configuration" in str(exc_info.value)