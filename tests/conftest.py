"""
Pytest configuration and shared fixtures for the test suite.
"""

import copy
import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any

# Test configuration
TEST_CONFIG = {
    'browser': {
        'headless': True,
        'timeout': 10000,
        'viewport': {'width': 1280, 'height': 720},
        'user_agent': 'EthicalScraper/1.0 (Test)'
    },
    'scraping': {
        'respect_robots': False,  # Disable for testing
        'delay_between_requests': 0.1,
        'max_concurrent_requests': 1,
        'max_requests_per_domain_per_minute': 100,  # Higher limit for testing
        'retry_attempts': 1,
        'retry_delay': 0.1
    },
    'output': {
        'format': 'json',
        'pretty_print': True,
        'include_metadata': True,
        'image_handling': 'absolute_urls'
    },
    'logging': {
        'level': 'DEBUG',
        'file': 'logs/test.log',
        'max_size_mb': 1,
        'backup_count': 2
    },
    'validation': {
        'min_content_length': 10,  # Lower for testing
        'max_content_length': 10000,
        'required_fields': ['title', 'content_html'],
        'image_url_validation': False
    }
}

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Test Heading</h1>
    <p>Test content for unit testing purposes.</p>
    <div class="content">
        <p>More test content with <a href="/test">links</a>.</p>
        <img src="/test.jpg" alt="Test image">
    </div>
</body>
</html>
"""

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return copy.deepcopy(TEST_CONFIG)

@pytest.fixture
def sample_html():
    """Provide sample HTML for testing."""
    return SAMPLE_HTML

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_config_file(temp_dir):
    """Create temporary config file."""
    import yaml
    config_file = temp_dir / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.safe_dump(TEST_CONFIG, f)
    return str(config_file)

@pytest.fixture
def mock_page():
    """Mock Playwright Page object."""
    page = AsyncMock()
    page.content.return_value = SAMPLE_HTML
    page.title.return_value = "Test Page"
    page.url = "https://example.com/test"
    return page

@pytest.fixture
def mock_browser_context():
    """Mock browser context."""
    context = AsyncMock()
    context.new_page.return_value = mock_page()
    return context

@pytest.fixture
def mock_browser():
    """Mock Playwright Browser object."""
    browser = AsyncMock()
    browser.new_context.return_value = mock_browser_context()
    return browser

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_robots_parser():
    """Mock RobotFileParser."""
    parser = MagicMock()
    parser.can_fetch.return_value = True
    return parser

@pytest.fixture
def sample_scraped_content():
    """Sample ScrapedContent for testing."""
    from scraper import ScrapedContent
    return ScrapedContent(
        title="Test Title",
        slug="test-title",
        source_url="https://example.com/test",
        content_html="<h1>Test</h1><p>Content</p>",
        images=["https://example.com/test.jpg"],
        scraped_at="2025-08-27T00:00:00.000000Z",
        metadata={
            'title': 'Test Title',
            'url': 'https://example.com/test',
            'selector': 'body',
            'scrape_duration': 1.5,
            'image_count': 1,
            'content_length': 25
        }
    )

class MockResponse:
    """Mock HTTP response."""
    def __init__(self, status_code=200, text="", json_data=None):
        self.status_code = status_code
        self._text = text
        self._json_data = json_data or {}
    
    def text(self):
        return self._text
    
    def json(self):
        return self._json_data