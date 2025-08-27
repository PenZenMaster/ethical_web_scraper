"""
Unit tests for image_manager.py module.
Tests the ImageManager class and image processing functionality.
"""

import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import tempfile
import shutil
import os

from image_manager import ImageManager, ImageInfo
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
        assert image_info.filename == "image.jpg"
    
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
        assert data['filename'] == "image.jpg"


class TestImageManager:
    """Test ImageManager class."""
    
    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing."""
        return {
            'output': {
                'image_handling': 'absolute_urls'
            },
            'image_settings': {
                'download_directory': 'test_images',
                'organize_by_domain': True,
                'max_image_size': '5MB',
                'allowed_formats': ['jpg', 'png', 'gif']
            },
            'browser': {
                'user_agent': 'TestAgent/1.0'
            }
        }
    
    @pytest.fixture
    def download_config(self):
        """Configuration for download testing."""
        return {
            'output': {
                'image_handling': 'download_local'
            },
            'image_settings': {
                'download_directory': 'test_images',
                'organize_by_domain': True,
                'max_image_size': '5MB',
                'allowed_formats': ['jpg', 'png', 'gif'],
                'timeout': 30
            },
            'browser': {
                'user_agent': 'TestAgent/1.0'
            }
        }
    
    def test_image_manager_initialization(self, basic_config):
        """Test ImageManager initialization."""
        manager = ImageManager(basic_config)
        
        assert manager.handling_mode == 'absolute_urls'
        assert manager.base_directory == Path('test_images')
        assert manager.organize_by_domain is True
        assert manager.max_file_size == 5 * 1024 * 1024  # 5MB
        assert 'jpg' in manager.allowed_formats
    
    def test_parse_size(self, basic_config):
        """Test size parsing functionality."""
        manager = ImageManager(basic_config)
        
        assert manager._parse_size('1MB') == 1024 * 1024
        assert manager._parse_size('500KB') == 500 * 1024
        assert manager._parse_size('2GB') == 2 * 1024 * 1024 * 1024
        assert manager._parse_size(12345) == 12345
        assert manager._parse_size('1000') == 1000
    
    def test_get_safe_filename(self, basic_config):
        """Test safe filename generation."""
        manager = ImageManager(basic_config)
        
        # URL with filename
        filename = manager._get_safe_filename(
            "https://example.com/images/test-image.jpg"
        )
        assert filename == "test-image.jpg"
        
        # URL without clear filename
        filename = manager._get_safe_filename(
            "https://example.com/dynamic?id=123",
            "image/png"
        )
        assert filename.startswith("image_")
        assert filename.endswith(".png")
    
    def test_get_storage_path(self, basic_config):
        """Test storage path generation."""
        manager = ImageManager(basic_config)
        
        # With domain organization
        path = manager._get_storage_path(
            "https://example.com/image.jpg", 
            "image.jpg"
        )
        assert path == Path("test_images/example.com/image.jpg")
        
        # Without domain organization
        manager.organize_by_domain = False
        path = manager._get_storage_path(
            "https://example.com/image.jpg",
            "image.jpg"
        )
        assert path == Path("test_images/image.jpg")
    
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
    
    @patch('image_manager.urlopen')
    def test_download_image_success(self, mock_urlopen, download_config):
        """Test successful image download."""
        manager = ImageManager(download_config)
        
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.headers = {
            'Content-Type': 'image/jpeg',
            'Content-Length': '12345'
        }
        mock_response.read.return_value = b'fake_image_data'
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Mock file system operations
        with patch('pathlib.Path.mkdir'), \
             patch('builtins.open', mock_open()) as mock_file:
            
            result = manager.download_image("https://example.com/test.jpg")
            
            assert result.downloaded is True
            assert result.original_url == "https://example.com/test.jpg"
            assert result.file_size == 15  # len(b'fake_image_data')
            assert result.mime_type == 'image/jpeg'
            assert "test.jpg" in result.local_path
    
    @patch('image_manager.urlopen')
    def test_download_image_failure(self, mock_urlopen, download_config):
        """Test image download failure handling."""
        manager = ImageManager(download_config)
        
        # Mock HTTP error
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            "https://example.com/test.jpg", 
            404, 
            "Not Found", 
            {}, 
            None
        )
        
        result = manager.download_image("https://example.com/test.jpg")
        
        assert result.downloaded is False
        assert result.error is not None
        assert "404" in result.error
    
    def test_update_html_content(self, basic_config):
        """Test HTML content updating with new image URLs."""
        manager = ImageManager(basic_config)
        
        html_content = '''
        <div>
            <img src="https://example.com/old.jpg" alt="Test">
            <img src='https://example.com/old2.png' alt="Test2">
        </div>
        '''
        
        # Mock image mapping with downloaded images
        image_mapping = {
            "https://example.com/old.jpg": ImageInfo(
                original_url="https://example.com/old.jpg",
                local_path="images/example.com/old.jpg",
                downloaded=True
            ),
            "https://example.com/old2.png": ImageInfo(
                original_url="https://example.com/old2.png", 
                local_path="images/example.com/old2.png",
                downloaded=True
            )
        }
        
        # Set to download_local mode for URL replacement
        manager.handling_mode = 'download_local'
        
        updated_html = manager.update_html_content(html_content, image_mapping)
        
        assert 'src="images/example.com/old.jpg"' in updated_html
        assert "src='images/example.com/old2.png'" in updated_html
        assert "https://example.com/old.jpg" not in updated_html
    
    def test_get_statistics(self, basic_config):
        """Test statistics gathering."""
        manager = ImageManager(basic_config)
        
        # Simulate some processing
        manager.stats['attempted'] = 5
        manager.stats['successful'] = 4
        manager.stats['failed'] = 1
        manager.stats['total_size'] = 12345
        
        stats = manager.get_statistics()
        
        assert stats['images_attempted'] == 5
        assert stats['images_successful'] == 4
        assert stats['images_failed'] == 1
        assert stats['total_downloaded_size'] == 12345
        assert stats['success_rate'] == 80.0  # 4/5 * 100
        assert stats['handling_mode'] == 'absolute_urls'
    
    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_cleanup_failed_downloads(self, mock_exists, mock_rglob, basic_config):
        """Test cleanup of failed download files."""
        manager = ImageManager(basic_config)
        
        # Mock directory exists
        mock_exists.return_value = True
        
        # Mock empty files
        mock_empty_file = MagicMock()
        mock_empty_file.is_file.return_value = True
        mock_empty_file.stat.return_value.st_size = 0
        mock_empty_file.unlink.return_value = None
        
        mock_good_file = MagicMock()
        mock_good_file.is_file.return_value = True
        mock_good_file.stat.return_value.st_size = 12345
        
        mock_rglob.return_value = [mock_empty_file, mock_good_file, mock_empty_file]
        
        manager.cleanup_failed_downloads()
        
        # Should unlink empty files
        assert mock_empty_file.unlink.call_count == 2
        mock_good_file.unlink.assert_not_called()


class TestImageManagerIntegration:
    """Integration tests for ImageManager."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_full_workflow_absolute_urls(self, temp_dir):
        """Test complete workflow in absolute_urls mode."""
        config = {
            'output': {'image_handling': 'absolute_urls'},
            'image_settings': {
                'download_directory': temp_dir,
                'organize_by_domain': False
            },
            'browser': {'user_agent': 'TestAgent/1.0'}
        }
        
        manager = ImageManager(config)
        
        image_urls = [
            "https://example.com/image1.jpg",
            "https://test.com/image2.png"
        ]
        
        alt_texts = {
            "https://example.com/image1.jpg": "First image",
            "https://test.com/image2.png": "Second image"
        }
        
        results = manager.process_images(image_urls, alt_texts)
        
        assert len(results) == 2
        for url, result in results.items():
            assert result.original_url == url
            assert result.alt_text == alt_texts[url]
            assert result.downloaded is False  # Not downloaded in absolute_urls mode
        
        stats = manager.get_statistics()
        assert stats['handling_mode'] == 'absolute_urls'