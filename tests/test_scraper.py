"""
Unit tests for scraper.py module.
Tests the EthicalScraper class and scraping functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.robotparser import RobotFileParser

from scraper import EthicalScraper, ScrapedContent, scrape_url, scrape_url_async
from exceptions import (
    ValidationException, RobotsException, RateLimitException,
    NetworkException, SelectorException
)


class TestScrapedContent:
    """Test ScrapedContent dataclass."""
    
    def test_scraped_content_creation(self):
        """Test ScrapedContent creation."""
        content = ScrapedContent(
            title="Test Title",
            slug="test-title", 
            source_url="https://example.com",
            content_html="<h1>Test</h1>",
            images=["https://example.com/image.jpg"],
            scraped_at="2025-08-27T00:00:00Z"
        )
        
        assert content.title == "Test Title"
        assert content.slug == "test-title"
        assert content.source_url == "https://example.com"
        assert len(content.images) == 1
        assert content.metadata == {}  # Default empty dict
    
    def test_scraped_content_with_metadata(self):
        """Test ScrapedContent with metadata."""
        metadata = {"duration": 1.5, "selector": "body"}
        content = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Test</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z",
            metadata=metadata
        )
        
        assert content.metadata == metadata
        assert content.metadata["duration"] == 1.5


class TestEthicalScraperInitialization:
    """Test EthicalScraper initialization."""
    
    def test_scraper_init_with_config_dict(self, test_config):
        """Test scraper initialization with config dictionary."""
        scraper = EthicalScraper(test_config)
        
        assert scraper.respect_robots is False  # From test config
        assert scraper.delay_between_requests == 0.1
        assert scraper.retry_attempts == 1
    
    def test_scraper_init_with_config_path(self, temp_config_file):
        """Test scraper initialization with config file path."""
        scraper = EthicalScraper(temp_config_file)
        
        assert scraper.respect_robots is False
        assert scraper.user_agent == "EthicalScraper/1.0 (Test)"
    
    def test_scraper_init_with_invalid_config_type(self):
        """Test scraper initialization with invalid config type."""
        with pytest.raises(TypeError) as exc_info:
            EthicalScraper(123)  # Invalid type
        assert "config must be either a string path or dictionary" in str(exc_info.value)
    
    def test_scraper_init_rate_limiting_setup(self, test_config):
        """Test rate limiting setup during initialization."""
        scraper = EthicalScraper(test_config)
        
        assert scraper._max_requests_per_domain_per_minute == 100
        assert isinstance(scraper._domain_request_history, dict)


class TestURLValidation:
    """Test URL validation methods."""
    
    def test_validate_url_success(self, test_config):
        """Test successful URL validation."""
        scraper = EthicalScraper(test_config)
        
        # Should not raise exception
        result = scraper.validate_url("https://example.com")
        assert result is True
    
    def test_validate_url_invalid_scheme(self, test_config):
        """Test URL validation with invalid scheme."""
        scraper = EthicalScraper(test_config)
        
        with pytest.raises(ValidationException) as exc_info:
            scraper.validate_url("ftp://example.com")
        assert "Invalid URL format" in str(exc_info.value)
    
    def test_validate_url_malformed(self, test_config):
        """Test URL validation with malformed URL."""
        scraper = EthicalScraper(test_config)
        
        with pytest.raises(ValidationException) as exc_info:
            scraper.validate_url("not-a-url")
        assert "Invalid URL format" in str(exc_info.value)


class TestRobotsValidation:
    """Test robots.txt validation."""
    
    @pytest.mark.asyncio
    async def test_robots_validation_disabled(self, test_config):
        """Test robots validation when disabled."""
        scraper = EthicalScraper(test_config)  # respect_robots = False
        
        result = await scraper.validate_robots_txt("https://example.com/test")
        assert result is True
    
    @pytest.mark.asyncio
    async def test_robots_validation_allowed(self, test_config):
        """Test robots validation when allowed."""
        test_config['scraping']['respect_robots'] = True
        scraper = EthicalScraper(test_config)
        
        # Mock successful robots.txt check
        with patch.object(scraper, '_robots_cache', {"https://example.com/robots.txt": MagicMock()}):
            mock_parser = scraper._robots_cache["https://example.com/robots.txt"]
            mock_parser.can_fetch.return_value = True
            
            result = await scraper.validate_robots_txt("https://example.com/test")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_robots_validation_disallowed(self, test_config):
        """Test robots validation when disallowed."""
        test_config['scraping']['respect_robots'] = True
        scraper = EthicalScraper(test_config)
        
        # Mock robots.txt that disallows scraping
        with patch.object(scraper, '_robots_cache', {"https://example.com/robots.txt": MagicMock()}):
            mock_parser = scraper._robots_cache["https://example.com/robots.txt"]
            mock_parser.can_fetch.return_value = False
            
            with pytest.raises(RobotsException) as exc_info:
                await scraper.validate_robots_txt("https://example.com/test")
            assert "disallows scraping" in str(exc_info.value)
    
    @pytest.mark.asyncio 
    async def test_robots_validation_no_robots_file(self, test_config):
        """Test robots validation with missing robots.txt."""
        test_config['scraping']['respect_robots'] = True
        scraper = EthicalScraper(test_config)
        
        # Mock RobotFileParser that raises exception (no robots.txt)
        with patch('scraper.RobotFileParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.read.side_effect = Exception("HTTP 404")
            mock_parser_class.return_value = mock_parser
            
            result = await scraper.validate_robots_txt("https://example.com/test")
            assert result is True  # Should allow when no robots.txt


class TestRateLimiting:
    """Test domain rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting_first_request(self, test_config):
        """Test rate limiting for first request to domain."""
        scraper = EthicalScraper(test_config)
        
        result = await scraper.check_domain_rate_limit("https://example.com/test")
        assert result is True
        assert "example.com" in scraper._domain_request_history
    
    @pytest.mark.asyncio
    async def test_rate_limiting_within_limit(self, test_config):
        """Test rate limiting within allowed limit."""
        test_config['scraping']['max_requests_per_domain_per_minute'] = 5
        scraper = EthicalScraper(test_config)
        
        # Make multiple requests within limit
        for i in range(4):
            result = await scraper.check_domain_rate_limit("https://example.com/test")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limiting_exceeded(self, test_config):
        """Test rate limiting when limit is exceeded."""
        test_config['scraping']['max_requests_per_domain_per_minute'] = 2
        scraper = EthicalScraper(test_config)
        
        # Make requests up to limit
        await scraper.check_domain_rate_limit("https://example.com/test1")
        await scraper.check_domain_rate_limit("https://example.com/test2")
        
        # Next request should raise exception
        with pytest.raises(RateLimitException) as exc_info:
            await scraper.check_domain_rate_limit("https://example.com/test3")
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.domain == "example.com"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_cleanup_old_requests(self, test_config):
        """Test that old requests are cleaned up."""
        scraper = EthicalScraper(test_config)
        
        # Manually add old request (older than 60 seconds)
        import time
        old_time = time.time() - 70  # 70 seconds ago
        scraper._domain_request_history["example.com"] = [old_time] * 50
        
        # New request should not be rate limited
        result = await scraper.check_domain_rate_limit("https://example.com/test")
        assert result is True
        
        # Old requests should be cleaned up
        assert len(scraper._domain_request_history["example.com"]) == 1


class TestContentValidation:
    """Test content validation methods."""
    
    def test_content_validation_success(self, test_config, sample_scraped_content):
        """Test successful content validation."""
        scraper = EthicalScraper(test_config)
        
        result = scraper.validate_content(sample_scraped_content)
        assert result is True
    
    def test_content_validation_too_short(self, test_config):
        """Test content validation with content too short."""
        test_config['validation']['min_content_length'] = 100
        scraper = EthicalScraper(test_config)
        
        content = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<p>Short</p>",  # Only ~11 chars
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        
        with pytest.raises(ValidationException) as exc_info:
            scraper.validate_content(content)
        assert "Content too short" in str(exc_info.value)
    
    def test_content_validation_too_long(self, test_config):
        """Test content validation with content too long."""
        test_config['validation']['max_content_length'] = 50
        scraper = EthicalScraper(test_config)
        
        long_content = "<p>" + "x" * 100 + "</p>"  # Much longer than 50 chars
        content = ScrapedContent(
            title="Test",
            slug="test", 
            source_url="https://example.com",
            content_html=long_content,
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        
        with pytest.raises(ValidationException) as exc_info:
            scraper.validate_content(content)
        assert "Content too long" in str(exc_info.value)
    
    def test_content_validation_missing_required_field(self, test_config):
        """Test content validation with missing required field."""
        scraper = EthicalScraper(test_config)
        
        content = ScrapedContent(
            title="",  # Empty title (required field)
            slug="test",
            source_url="https://example.com",
            content_html="<p>Valid content here</p>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        
        with pytest.raises(ValidationException) as exc_info:
            scraper.validate_content(content)
        assert "Required field 'title'" in str(exc_info.value)


class TestScrapingProcess:
    """Test the main scraping process."""
    
    @pytest.mark.asyncio
    @patch('scraper.BrowserManager')
    async def test_scrape_url_success(self, mock_browser_manager, test_config, mock_page):
        """Test successful URL scraping."""
        scraper = EthicalScraper(test_config)
        
        # Mock browser manager
        mock_browser_manager.return_value.__aenter__.return_value.get_page = AsyncMock(return_value=mock_page)
        mock_page.title.return_value = "Test Page"
        mock_page.content.return_value = "<html><body><h1>Test</h1></body></html>"
        
        # Mock extract_content
        with patch('scraper.extract_content') as mock_extract:
            mock_extract.return_value = ("<h1>Test</h1>", [])
            
            result = await scraper.scrape_url("https://example.com", "h1")
            
            assert isinstance(result, ScrapedContent)
            assert result.title == "Test Page"
            assert result.source_url == "https://example.com"
            assert "<h1>Test</h1>" in result.content_html
    
    @pytest.mark.asyncio
    async def test_scrape_url_validation_error(self, test_config):
        """Test scraping with URL validation error."""
        scraper = EthicalScraper(test_config)
        
        with pytest.raises(ValidationException):
            await scraper.scrape_url("invalid-url", "body")
    
    @pytest.mark.asyncio
    async def test_scrape_url_robots_error(self, test_config):
        """Test scraping with robots.txt error."""
        test_config['scraping']['respect_robots'] = True
        scraper = EthicalScraper(test_config)
        
        # Mock robots validation to raise exception
        with patch.object(scraper, 'validate_robots_txt', side_effect=RobotsException("Disallowed")):
            with pytest.raises(RobotsException):
                await scraper.scrape_url("https://example.com", "body")
    
    @pytest.mark.asyncio
    async def test_scrape_url_rate_limit_error(self, test_config):
        """Test scraping with rate limit error."""
        scraper = EthicalScraper(test_config)
        
        # Mock rate limiting to raise exception
        with patch.object(scraper, 'check_domain_rate_limit', side_effect=RateLimitException("Rate limited")):
            with pytest.raises(RateLimitException):
                await scraper.scrape_url("https://example.com", "body")


class TestBatchScraping:
    """Test batch scraping functionality."""
    
    @pytest.mark.asyncio
    @patch('scraper.BrowserManager')
    async def test_batch_scrape_success(self, mock_browser_manager, test_config, mock_page):
        """Test successful batch scraping."""
        scraper = EthicalScraper(test_config)
        
        # Mock browser manager
        mock_browser_manager.return_value.__aenter__.return_value.get_page = AsyncMock(return_value=mock_page)
        mock_page.title.return_value = "Test Page"
        mock_page.content.return_value = "<html><body><h1>Test</h1></body></html>"
        
        # Mock extract_content
        with patch('scraper.extract_content') as mock_extract:
            mock_extract.return_value = ("<h1>Test</h1>", [])
            
            urls = ["https://example.com/1", "https://example.com/2"]
            results = await scraper.batch_scrape(urls, "h1")
            
            assert len(results) == 2
            assert all(isinstance(r, ScrapedContent) for r in results)
    
    @pytest.mark.asyncio
    async def test_batch_scrape_with_failures(self, test_config):
        """Test batch scraping with some failures."""
        scraper = EthicalScraper(test_config)
        
        # Mock scrape_url to fail for second URL
        async def mock_scrape_url(url, selector, **kwargs):
            if "fail" in url:
                raise NetworkException("Network error")
            return ScrapedContent(
                title="Test",
                slug="test",
                source_url=url,
                content_html="<h1>Test</h1>",
                images=[],
                scraped_at="2025-08-27T00:00:00Z"
            )
        
        with patch.object(scraper, 'scrape_url', side_effect=mock_scrape_url):
            urls = ["https://example.com/good", "https://example.com/fail"]
            results = await scraper.batch_scrape(urls, "h1")
            
            # Should return only successful results
            assert len(results) == 1
            assert results[0].source_url == "https://example.com/good"


class TestModuleFunctions:
    """Test module-level convenience functions."""
    
    @patch('scraper.EthicalScraper')
    def test_scrape_url_sync_function(self, mock_scraper_class):
        """Test synchronous scrape_url function."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        
        # Mock the async scrape_url method
        expected_result = ScrapedContent(
            title="Test",
            slug="test",
            source_url="https://example.com",
            content_html="<h1>Test</h1>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        
        with patch('asyncio.run') as mock_run:
            mock_run.return_value = expected_result
            
            result = scrape_url("https://example.com", "h1")
            
            assert result == expected_result
            mock_scraper_class.assert_called_once_with("config/default.yaml")
    
    @pytest.mark.asyncio
    @patch('scraper.EthicalScraper')
    async def test_scrape_url_async_function(self, mock_scraper_class):
        """Test asynchronous scrape_url_async function."""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        
        expected_result = ScrapedContent(
            title="Test",
            slug="test", 
            source_url="https://example.com",
            content_html="<h1>Test</h1>",
            images=[],
            scraped_at="2025-08-27T00:00:00Z"
        )
        mock_scraper.scrape_url = AsyncMock(return_value=expected_result)
        
        result = await scrape_url_async("https://example.com", "h1")
        
        assert result == expected_result
        mock_scraper.scrape_url.assert_called_once_with("https://example.com", "h1")


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    @pytest.mark.asyncio
    async def test_scraping_continues_after_rate_limit(self, test_config):
        """Test that scraping can continue after rate limit cleanup."""
        test_config['scraping']['max_requests_per_domain_per_minute'] = 1
        scraper = EthicalScraper(test_config)
        
        # First request should succeed
        await scraper.check_domain_rate_limit("https://example.com/test1")
        
        # Second request should fail
        with pytest.raises(RateLimitException):
            await scraper.check_domain_rate_limit("https://example.com/test2")
        
        # After cleaning up old requests (mock time passage)
        import time
        current_time = time.time()
        scraper._domain_request_history["example.com"] = [current_time - 70]  # Old request
        
        # New request should succeed
        result = await scraper.check_domain_rate_limit("https://example.com/test3")
        assert result is True


class TestImageManagement:
    """Test image management integration."""
    
    def test_scraped_content_with_image_info(self):
        """Test ScrapedContent with image_info field."""
        image_info = {
            "https://example.com/image.jpg": {
                "original_url": "https://example.com/image.jpg",
                "local_path": "/images/example.com/image.jpg",
                "downloaded": True,
                "file_size": 12345
            }
        }
        
        content = ScrapedContent(
            title="Test Title",
            slug="test-title",
            source_url="https://example.com",
            content_html="<h1>Test</h1>",
            images=["https://example.com/image.jpg"],
            scraped_at="2025-08-27T00:00:00Z",
            image_info=image_info
        )
        
        assert content.image_info == image_info
        assert "https://example.com/image.jpg" in content.image_info
        assert content.image_info["https://example.com/image.jpg"]["downloaded"] is True

    def test_extract_alt_texts(self, test_config):
        """Test alt text extraction from HTML."""
        scraper = EthicalScraper(test_config)
        
        html_content = '''
        <html>
        <body>
            <img src="https://example.com/image1.jpg" alt="Test Image 1">
            <img src="/relative/image2.png" alt="Test Image 2">
            <img src="https://example.com/image3.gif">  <!-- No alt -->
        </body>
        </html>
        '''
        
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/relative/image2.png", 
            "https://example.com/image3.gif"
        ]
        
        alt_texts = scraper._extract_alt_texts(html_content, image_urls)
        
        assert "https://example.com/image1.jpg" in alt_texts
        assert alt_texts["https://example.com/image1.jpg"] == "Test Image 1"
        assert "https://example.com/image3.gif" not in alt_texts  # No alt text

    @pytest.mark.asyncio
    @patch('scraper.BrowserManager')
    @patch('scraper.extract_content')
    async def test_scrape_with_image_processing(self, mock_extract_content, mock_browser_manager, test_config):
        """Test complete scrape with image processing."""
        # Configure for image downloading
        test_config['output']['image_handling'] = 'download_local'
        test_config['image_settings'] = {
            'download_directory': 'test_images',
            'organize_by_domain': True
        }
        
        scraper = EthicalScraper(test_config)
        
        # Mock browser
        mock_page = AsyncMock()
        mock_browser = AsyncMock()
        mock_browser.get_page.return_value = mock_page
        mock_browser.render_content.return_value = '<html><img src="/test.jpg" alt="Test"></html>'
        mock_browser.get_page_metadata.return_value = {'title': 'Test Page'}
        mock_browser_manager.return_value.__aenter__.return_value = mock_browser
        
        # Mock content extraction
        mock_extract_content.return_value = (
            '<p>Test content <img src="https://example.com/test.jpg" alt="Test"></p>',
            ['https://example.com/test.jpg']
        )
        
        # Mock image manager to avoid actual downloads in tests
        with patch.object(scraper.image_manager, 'process_images') as mock_process_images:
            with patch.object(scraper.image_manager, 'update_html_content') as mock_update_html:
                with patch.object(scraper.image_manager, 'get_statistics') as mock_get_stats:
                    # Configure mocks
                    mock_process_images.return_value = {
                        'https://example.com/test.jpg': MagicMock(
                            to_dict=MagicMock(return_value={
                                'original_url': 'https://example.com/test.jpg',
                                'downloaded': True,
                                'local_path': 'test_images/example.com/test.jpg'
                            })
                        )
                    }
                    mock_update_html.return_value = '<p>Test content <img src="test_images/example.com/test.jpg" alt="Test"></p>'
                    mock_get_stats.return_value = {
                        'images_attempted': 1,
                        'images_successful': 1,
                        'handling_mode': 'download_local'
                    }
                    
                    # Run scrape
                    result = await scraper.scrape_url("https://example.com", "body")
                    
                    # Assertions
                    assert result.title == "Test Page"
                    assert result.images == ['https://example.com/test.jpg']
                    assert result.image_info is not None
                    assert 'https://example.com/test.jpg' in result.image_info
                    assert result.metadata['image_processing']['handling_mode'] == 'download_local'
                    
                    # Verify image manager was called
                    mock_process_images.assert_called_once()
                    mock_update_html.assert_called_once()
                    mock_get_stats.assert_called_once()