"""
Unit tests for main.py CLI module.
Tests CLI commands and integration functionality.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from typer.testing import CliRunner

from main import app, _scrape_single, _scrape_batch, _display_summary
from scraper import ScrapedContent


class TestCLICommands:
    """Test CLI command functionality."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    @patch('main.setup_logging')
    @patch('main.load_config') 
    @patch('main.asyncio.run')
    def test_scrape_command_basic(self, mock_run, mock_load_config, mock_setup_logging):
        """Test basic scrape command."""
        # Mock dependencies
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        
        # Mock scraped content
        mock_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        # Mock exporter
        with patch('main.ContentExporter') as mock_exporter:
            mock_exporter.return_value.export_json.return_value = "test_output.json"
            
            result = self.runner.invoke(app, ['scrape', 'https://example.com'])
            
            assert result.exit_code == 0
            assert "Starting scrape" in result.stdout
            assert "Exported JSON" in result.stdout
    
    def test_scrape_command_help(self):
        """Test scrape command help."""
        result = self.runner.invoke(app, ['scrape', '--help'])
        
        assert result.exit_code == 0
        assert "URL to scrape" in result.stdout
        assert "--selector" in result.stdout
        assert "--format" in result.stdout
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_scrape_command_with_options(self, mock_run, mock_load_config, mock_setup_logging):
        """Test scrape command with various options."""
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        
        mock_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        with patch('main.ContentExporter') as mock_exporter:
            mock_exporter.return_value.export_json.return_value = "custom_output.json"
            
            result = self.runner.invoke(app, [
                'scrape', 
                'https://example.com',
                '--selector', 'h1',
                '--output', 'custom_output',
                '--format', 'json',
                '--verbose'
            ])
            
            assert result.exit_code == 0
            mock_load_config.assert_called_once_with(None)  # No config file specified
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_scrape_command_all_formats(self, mock_run, mock_load_config, mock_setup_logging):
        """Test scrape command with all export formats."""
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        
        mock_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        with patch('main.ContentExporter') as mock_exporter:
            mock_instance = mock_exporter.return_value
            mock_instance.export_json.return_value = "output.json"
            mock_instance.export_csv.return_value = "output.csv"
            mock_instance.export_xml.return_value = "output.xml"
            
            result = self.runner.invoke(app, [
                'scrape',
                'https://example.com',
                '--format', 'all'
            ])
            
            assert result.exit_code == 0
            assert "Exported JSON" in result.stdout
            assert "Exported CSV" in result.stdout  
            assert "Exported XML" in result.stdout
    
    def test_batch_command_help(self):
        """Test batch command help."""
        result = self.runner.invoke(app, ['batch', '--help'])
        
        assert result.exit_code == 0
        assert "URLs from a file" in result.stdout
        assert "--output-dir" in result.stdout
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_batch_command_success(self, mock_run, mock_load_config, mock_setup_logging, temp_dir):
        """Test successful batch command."""
        # Create URLs file
        urls_file = temp_dir / "urls.txt"
        urls_file.write_text("https://example.com/1\\nhttps://example.com/2\\n")
        
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        
        # Mock batch results
        mock_results = [
            ScrapedContent(
                title="Test 1",
                slug="test-1",
                source_url="https://example.com/1",
                content_html="<p>Test 1</p>",
                images=[],
                scraped_at="2025-08-27T00:00:00Z"
            )
        ]
        mock_run.return_value = mock_results
        
        with patch('main.ContentExporter') as mock_exporter:
            mock_exporter.return_value.export_json.return_value = "batch_results.json"
            
            result = self.runner.invoke(app, [
                'batch',
                str(urls_file),
                '--format', 'json'
            ])
            
            assert result.exit_code == 0
            assert "Found 2 URLs" in result.stdout
            assert "Batch export complete" in result.stdout
    
    def test_batch_command_file_not_found(self):
        """Test batch command with non-existent URLs file."""
        result = self.runner.invoke(app, [
            'batch',
            'nonexistent_file.txt'
        ])
        
        assert result.exit_code == 1
        assert "URLs file not found" in result.stdout
    
    @patch('main.setup_logging')
    @patch('main.asyncio.run')
    def test_test_command_success(self, mock_run, mock_setup_logging):
        """Test successful test command."""
        mock_setup_logging.return_value = MagicMock()
        
        mock_result = ScrapedContent(
            title="Test Page",
            slug="test-page",
            source_url="https://httpbin.org/html",
            content_html="<p>Test content</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        result = self.runner.invoke(app, ['test'])
        
        assert result.exit_code == 0
        assert "Running scraper test" in result.stdout
        assert "Test successful" in result.stdout
    
    @patch('main.setup_logging')
    @patch('main.asyncio.run')
    def test_test_command_failure(self, mock_run, mock_setup_logging):
        """Test test command failure."""
        mock_setup_logging.return_value = MagicMock()
        mock_run.side_effect = Exception("Test error")
        
        result = self.runner.invoke(app, ['test'])
        
        assert result.exit_code == 1
        assert "Test failed" in result.stdout


class TestHelperFunctions:
    """Test CLI helper functions."""
    
    @pytest.mark.asyncio
    async def test_scrape_single_success(self, test_config):
        """Test _scrape_single helper function."""
        with patch('main.EthicalScraper') as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper_class.return_value = mock_scraper
            
            expected_result = ScrapedContent(
                title="Test",
                slug="test",
                source_url="https://example.com",
                content_html="<p>Test</p>",
                images=[],
                scraped_at="2025-08-27T00:00:00Z"
            )
            mock_scraper.scrape_url = AsyncMock(return_value=expected_result)
            
            result = await _scrape_single("https://example.com", "body", test_config)
            
            assert result == expected_result
            mock_scraper.scrape_url.assert_called_once_with("https://example.com", "body")
    
    @pytest.mark.asyncio
    async def test_scrape_single_no_config(self):
        """Test _scrape_single with no config provided."""
        with patch('main.load_config') as mock_load_config:
            with patch('main.EthicalScraper') as mock_scraper_class:
                mock_load_config.return_value = {'default': 'config'}
                mock_scraper = AsyncMock()
                mock_scraper_class.return_value = mock_scraper
                
                expected_result = ScrapedContent(
                    title="Test",
                    slug="test",
                    source_url="https://example.com",
                    content_html="<p>Test</p>",
                    images=[],
                    scraped_at="2025-08-27T00:00:00Z"
                )
                mock_scraper.scrape_url = AsyncMock(return_value=expected_result)
                
                result = await _scrape_single("https://example.com", "body")
                
                assert result == expected_result
                mock_load_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scrape_batch_success(self, test_config):
        """Test _scrape_batch helper function."""
        urls = ["https://example.com/1", "https://example.com/2"]
        
        with patch('main.EthicalScraper') as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper_class.return_value = mock_scraper
            
            # Mock successful scraping for both URLs
            results = [
                ScrapedContent(
                    title=f"Test {i}",
                    slug=f"test-{i}",
                    source_url=f"https://example.com/{i}",
                    content_html=f"<p>Test {i}</p>",
                    images=[],
                    scraped_at="2025-08-27T00:00:00Z"
                ) for i in [1, 2]
            ]
            mock_scraper.scrape_url = AsyncMock(side_effect=results)
            
            batch_results = await _scrape_batch(urls, "body", test_config)
            
            assert len(batch_results) == 2
            assert batch_results[0].title == "Test 1"
            assert batch_results[1].title == "Test 2"
    
    @pytest.mark.asyncio
    async def test_scrape_batch_with_failures(self, test_config):
        """Test _scrape_batch with some failures."""
        urls = ["https://example.com/success", "https://example.com/fail"]
        
        with patch('main.EthicalScraper') as mock_scraper_class:
            mock_scraper = AsyncMock()
            mock_scraper_class.return_value = mock_scraper
            
            # Mock one success, one failure
            def mock_scrape_side_effect(url, selector):
                if "fail" in url:
                    raise Exception("Scraping failed")
                return ScrapedContent(
                    title="Success",
                    slug="success",
                    source_url=url,
                    content_html="<p>Success</p>",
                    images=[],
                    scraped_at="2025-08-27T00:00:00Z"
                )
            
            mock_scraper.scrape_url = AsyncMock(side_effect=mock_scrape_side_effect)
            
            batch_results = await _scrape_batch(urls, "body", test_config)
            
            # Should return only successful results
            assert len(batch_results) == 1
            assert batch_results[0].title == "Success"
    
    def test_display_summary(self, sample_scraped_content):
        """Test _display_summary helper function."""
        # Add metadata for testing
        sample_scraped_content.metadata = {'scrape_duration': 1.23}
        
        # This should not raise any exceptions
        _display_summary(sample_scraped_content)
        # Note: We can't easily test the rich output without more complex mocking


class TestErrorHandling:
    """Test CLI error handling."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_scrape_command_ews_exception(self, mock_run, mock_load_config, mock_setup_logging):
        """Test scrape command with EWS exception."""
        from exceptions import ValidationException
        
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        mock_run.side_effect = ValidationException("Invalid content")
        
        with patch('main.handle_exception') as mock_handle:
            result = self.runner.invoke(app, ['scrape', 'https://example.com'])
            
            assert result.exit_code == 1
            mock_handle.assert_called_once()
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_scrape_command_unexpected_exception(self, mock_run, mock_load_config, mock_setup_logging):
        """Test scrape command with unexpected exception."""
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        mock_run.side_effect = RuntimeError("Unexpected error")
        
        result = self.runner.invoke(app, ['scrape', 'https://example.com'])
        
        assert result.exit_code == 1
        assert "Unexpected error" in result.stdout
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_scrape_command_no_result(self, mock_run, mock_load_config, mock_setup_logging):
        """Test scrape command when no result is returned."""
        mock_load_config.return_value = {'test': 'config'}
        mock_setup_logging.return_value = MagicMock()
        mock_run.return_value = None  # No result
        
        result = self.runner.invoke(app, ['scrape', 'https://example.com'])
        
        assert result.exit_code == 1
        assert "Scraping failed - no content returned" in result.stdout


class TestConfigurationHandling:
    """Test CLI configuration handling."""
    
    def setup_method(self):
        """Set up test runner."""
        self.runner = CliRunner()
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_custom_config_file(self, mock_run, mock_load_config, mock_setup_logging, temp_config_file):
        """Test using custom configuration file."""
        mock_load_config.return_value = {'custom': 'config'}
        mock_setup_logging.return_value = MagicMock()
        
        mock_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        with patch('main.ContentExporter') as mock_exporter:
            mock_exporter.return_value.export_json.return_value = "output.json"
            
            result = self.runner.invoke(app, [
                'scrape',
                'https://example.com',
                '--config', temp_config_file
            ])
            
            assert result.exit_code == 0
            mock_load_config.assert_called_once_with(temp_config_file)
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_robots_override(self, mock_run, mock_load_config, mock_setup_logging):
        """Test robots.txt override flag."""
        config = {'scraping': {'respect_robots_txt': True}}
        mock_load_config.return_value = config
        mock_setup_logging.return_value = MagicMock()
        
        mock_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        with patch('main.ContentExporter') as mock_exporter:
            mock_exporter.return_value.export_json.return_value = "output.json"
            
            result = self.runner.invoke(app, [
                'scrape',
                'https://example.com',
                '--no-robots'
            ])
            
            assert result.exit_code == 0
            # Config should be modified to disable robots
            assert config['scraping']['respect_robots_txt'] is False
    
    @patch('main.setup_logging')
    @patch('main.load_config')
    @patch('main.asyncio.run')
    def test_headless_override(self, mock_run, mock_load_config, mock_setup_logging):
        """Test headless mode override flag."""
        config = {'browser': {'headless': True}}
        mock_load_config.return_value = config
        mock_setup_logging.return_value = MagicMock()
        
        mock_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_run.return_value = mock_result
        
        with patch('main.ContentExporter') as mock_exporter:
            mock_exporter.return_value.export_json.return_value = "output.json"
            
            result = self.runner.invoke(app, [
                'scrape',
                'https://example.com',
                '--no-headless'
            ])
            
            assert result.exit_code == 0
            # Config should be modified to disable headless
            assert config['browser']['headless'] is False