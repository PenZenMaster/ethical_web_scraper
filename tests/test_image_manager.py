"""
Clean unit tests for image_manager.py module using modern modular API.
Tests the ImageManager class core functionality without legacy compatibility.
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock

from image_manager import ImageManager
from image_processing.format_handlers.download_local_handler import ImageInfo
from exceptions import ValidationException, NetworkException


class TestImageInfo:
    """Test ImageInfo dataclass."""
    
    def test_image_info_creation(self):
        """Test ImageInfo creation with basic parameters."""
        image_info = ImageInfo(
            original_url="https://example.com/image.jpg",
            local_path="/images/image.jpg",
            downloaded=True,
            file_size=12345
        )
        
        assert image_info.original_url == "https://example.com/image.jpg"
        assert image_info.local_path == "/images/image.jpg"
        assert image_info.downloaded is True
        assert image_info.file_size == 12345
    
    def test_image_info_to_dict(self):
        """Test ImageInfo serialization."""
        image_info = ImageInfo(
            original_url="https://example.com/image.jpg",
            local_path="/images/image.jpg",
            alt_text="Test image",
            downloaded=True,
            file_size=12345,
            mime_type="image/jpeg"
        )
        
        data = image_info.to_dict()
        
        assert data['original_url'] == "https://example.com/image.jpg"
        assert data['local_path'] == "/images/image.jpg"
        assert data['alt_text'] == "Test image"
        assert data['downloaded'] is True
        assert data['file_size'] == 12345
        assert data['mime_type'] == "image/jpeg"


class TestImageManager:
    """Test ImageManager class using modern modular API."""
    
    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing."""
        return {
            'output': {'image_handling': 'absolute_urls'},
            'image_settings': {
                'download_directory': 'test_images',
                'organize_by_domain': True,
                'max_image_size': '5MB',
                'allowed_formats': ['jpg', 'png', 'gif']
            },
            'browser': {'user_agent': 'TestAgent/1.0'}
        }
    
    def test_image_manager_initialization(self, basic_config):
        """Test ImageManager initialization."""
        manager = ImageManager(basic_config)
        
        assert manager.handling_mode == 'absolute_urls'
        assert 'absolute_urls' in manager.handlers
        assert 'download_local' in manager.handlers
        assert 'download_and_rehost' in manager.handlers
    
    def test_process_images_absolute_urls_mode(self, basic_config):
        """Test image processing in absolute_urls mode."""
        manager = ImageManager(basic_config)
        
        image_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.png"
        ]
        
        results = manager.process_images(image_urls)
        
        assert len(results) == 2
        assert "https://example.com/image1.jpg" in results
        assert "https://example.com/image2.png" in results
        
        # In absolute_urls mode, images are not downloaded
        for result in results.values():
            assert result.downloaded is False
            assert result.local_path is None
    
    def test_get_statistics(self, basic_config):
        """Test statistics gathering from handlers."""
        manager = ImageManager(basic_config)
        
        stats = manager.get_statistics()
        
        assert 'images_attempted' in stats
        assert 'images_successful' in stats
        assert 'images_failed' in stats
        assert 'handling_mode' in stats
        assert stats['handling_mode'] == 'absolute_urls'
    
    def test_cleanup_failed_downloads(self, basic_config):
        """Test cleanup delegation to storage manager."""
        manager = ImageManager(basic_config)
        
        # Should return 0 for absolute_urls mode (no storage manager)
        result = manager.cleanup_failed_downloads()
        assert result == 0
    
    def test_update_html_content(self, basic_config):
        """Test HTML content updating delegation."""
        manager = ImageManager(basic_config)
        
        html_content = '''
        <div>
            <img src="https://example.com/old.jpg" alt="Test">
        </div>
        '''
        
        image_mapping = {}
        
        # Should return processed HTML (delegated to HTML processor)
        result = manager.update_html_content(html_content, image_mapping)
        assert isinstance(result, str)
        assert 'img src' in result


class TestImageManagerIntegration:
    """Integration tests for ImageManager."""
    
    def test_full_workflow_absolute_urls(self):
        """Test complete workflow with absolute URLs."""
        config = {
            'output': {'image_handling': 'absolute_urls'},
            'image_settings': {'download_directory': 'images'},
            'browser': {'user_agent': 'TestAgent/1.0'}
        }
        
        manager = ImageManager(config)
        
        # Process some images
        urls = ["https://example.com/test1.jpg", "https://example.com/test2.png"]
        results = manager.process_images(urls)
        
        # Check results
        assert len(results) == 2
        for url in urls:
            assert url in results
            assert results[url].original_url == url
        
        # Update HTML
        html = '<img src="https://example.com/test1.jpg" alt="test">'
        updated = manager.update_html_content(html, results)
        assert isinstance(updated, str)
        
        # Get statistics
        stats = manager.get_statistics()
        assert isinstance(stats, dict)