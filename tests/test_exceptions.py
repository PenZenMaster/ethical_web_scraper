"""
Unit tests for exceptions.py module.
Tests all custom exception classes and error handling utilities.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch
from datetime import datetime

from exceptions import (
    EWSException, NetworkException, RenderException, SelectorException,
    ValidationException, RobotsException, RateLimitException, ConfigurationError,
    ERROR_CODE_MAP, handle_exception, create_exception_from_code
)


class TestBaseEWSException:
    """Test the base EWSException class."""
    
    def test_ews_exception_basic(self):
        """Test basic EWSException creation."""
        exc = EWSException("TEST001", "Test message")
        
        assert exc.code == "TEST001"
        assert exc.message == "Test message"
        assert exc.url is None
        assert exc.recovery_action is None
        assert str(exc) == "TEST001: Test message"
    
    def test_ews_exception_with_url(self):
        """Test EWSException with URL."""
        exc = EWSException("TEST001", "Test message", url="https://example.com")
        
        assert exc.url == "https://example.com"
        assert str(exc) == "TEST001: Test message (URL: https://example.com)"
    
    def test_ews_exception_with_recovery(self):
        """Test EWSException with recovery action."""
        exc = EWSException("TEST001", "Test message", recovery_action="Try again")
        
        assert exc.recovery_action == "Try again"
    
    def test_ews_exception_with_context(self):
        """Test EWSException with context data."""
        context = {"error_type": "test", "details": "test details"}
        exc = EWSException("TEST001", "Test message", context=context)
        
        assert exc.context == context
        assert exc.context["error_type"] == "test"
    
    def test_ews_exception_to_dict(self):
        """Test EWSException to_dict method."""
        exc = EWSException(
            "TEST001", 
            "Test message", 
            url="https://example.com",
            recovery_action="Try again",
            context={"test": "data"}
        )
        
        exc_dict = exc.to_dict()
        
        assert exc_dict["error_code"] == "TEST001"
        assert exc_dict["message"] == "Test message"
        assert exc_dict["url"] == "https://example.com"
        assert exc_dict["recovery_action"] == "Try again"
        assert exc_dict["context"] == {"test": "data"}
        assert "timestamp" in exc_dict
        assert exc_dict["exception_type"] == "EWSException"


class TestSpecificExceptions:
    """Test specific exception types."""
    
    def test_network_exception(self):
        """Test NetworkException (EWS001)."""
        exc = NetworkException("Connection timeout", url="https://example.com")
        
        assert exc.code == "EWS001"
        assert exc.message == "Connection timeout"
        assert exc.url == "https://example.com"
        assert "Check network connectivity" in exc.recovery_action
    
    def test_network_exception_with_status_code(self):
        """Test NetworkException with HTTP status code."""
        exc = NetworkException(
            "HTTP 404 Not Found", 
            url="https://example.com", 
            status_code=404
        )
        
        assert exc.context["status_code"] == 404
        assert exc.context["error_type"] == "http_error"
    
    def test_render_exception(self):
        """Test RenderException (EWS002)."""
        exc = RenderException("Page failed to load", url="https://example.com")
        
        assert exc.code == "EWS002"
        assert "page loading" in exc.recovery_action.lower()
    
    def test_render_exception_with_timeout(self):
        """Test RenderException with timeout."""
        exc = RenderException(
            "Page load timeout",
            url="https://example.com",
            timeout=30000
        )
        
        assert exc.context["timeout"] == 30000
    
    def test_selector_exception(self):
        """Test SelectorException (EWS003)."""
        exc = SelectorException(
            "Selector not found",
            url="https://example.com",
            selector=".nonexistent"
        )
        
        assert exc.code == "EWS003"
        assert exc.context["selector"] == ".nonexistent"
        assert "selector" in exc.recovery_action.lower()
    
    def test_validation_exception(self):
        """Test ValidationException (EWS004)."""
        exc = ValidationException(
            "Content too short",
            validation_type="content_length",
            expected_value=">= 100",
            actual_value=50
        )
        
        assert exc.code == "EWS004"
        assert exc.context["validation_type"] == "content_length"
        assert exc.context["expected_value"] == ">= 100"
        assert exc.context["actual_value"] == 50
    
    def test_robots_exception(self):
        """Test RobotsException (EWS005)."""
        exc = RobotsException(
            "Robots.txt disallows",
            url="https://example.com/page",
            user_agent="EthicalScraper/1.0"
        )
        
        assert exc.code == "EWS005"
        assert exc.context["user_agent"] == "EthicalScraper/1.0"
        assert "robots.txt" in exc.recovery_action.lower()
    
    def test_rate_limit_exception(self):
        """Test RateLimitException (EWS006)."""
        exc = RateLimitException(
            "Rate limit exceeded",
            domain="example.com",
            current_rate=25
        )
        
        assert exc.code == "EWS006"
        assert exc.context["domain"] == "example.com"
        assert exc.context["current_rate"] == 25
        assert "Wait before making" in exc.recovery_action
    
    def test_configuration_error(self):
        """Test ConfigurationError."""
        exc = ConfigurationError(
            "Missing section",
            config_path="/path/to/config.yaml",
            section="browser"
        )
        
        assert exc.code == "EWS_CONFIG"
        assert exc.config_path == "/path/to/config.yaml"
        assert exc.section == "browser"


class TestErrorCodeMapping:
    """Test error code mapping functionality."""
    
    def test_error_code_map_completeness(self):
        """Test that ERROR_CODE_MAP contains all exceptions."""
        expected_codes = ["EWS001", "EWS002", "EWS003", "EWS004", "EWS005", "EWS006"]
        
        for code in expected_codes:
            assert code in ERROR_CODE_MAP
    
    def test_create_exception_from_code_network(self):
        """Test creating NetworkException from code."""
        exc = create_exception_from_code("EWS001", "Test message")
        
        assert isinstance(exc, NetworkException)
        assert exc.code == "EWS001"
        assert exc.message == "Test message"
    
    def test_create_exception_from_code_validation(self):
        """Test creating ValidationException from code."""
        exc = create_exception_from_code(
            "EWS004", 
            "Validation failed",
            validation_type="test"
        )
        
        assert isinstance(exc, ValidationException)
        assert exc.context["validation_type"] == "test"
    
    def test_create_exception_from_code_unknown(self):
        """Test creating exception with unknown code."""
        exc = create_exception_from_code("EWS999", "Unknown error")
        
        assert isinstance(exc, EWSException)
        assert exc.code == "EWS999"


class TestExceptionHandling:
    """Test exception handling utilities."""
    
    def test_handle_exception_basic(self):
        """Test basic exception handling."""
        exc = NetworkException("Test error")
        logger = MagicMock(spec=logging.Logger)
        
        error_info = handle_exception(exc, logger, reraise=False)
        
        assert error_info["error_code"] == "EWS001"
        assert error_info["message"] == "Test error"
        assert "timestamp" in error_info
        logger.error.assert_called_once()
    
    def test_handle_exception_with_recovery(self):
        """Test exception handling with recovery action."""
        exc = ValidationException("Content invalid", recovery_action="Fix content")
        logger = MagicMock(spec=logging.Logger)
        
        handle_exception(exc, logger, reraise=False)
        
        logger.info.assert_called_with("Recovery suggestion: Fix content")
    
    def test_handle_exception_reraise(self):
        """Test exception handling with reraise."""
        exc = NetworkException("Test error")
        logger = MagicMock(spec=logging.Logger)
        
        with pytest.raises(NetworkException):
            handle_exception(exc, logger, reraise=True)
    
    def test_handle_exception_non_ews(self):
        """Test handling non-EWS exceptions."""
        exc = ValueError("Standard exception")
        logger = MagicMock(spec=logging.Logger)
        
        error_info = handle_exception(exc, logger, reraise=False)
        
        assert error_info["error_code"] == "UNKNOWN"
        assert error_info["exception_type"] == "ValueError"
    
    def test_handle_exception_no_logger(self):
        """Test exception handling without logger."""
        exc = NetworkException("Test error")
        
        # Should not raise even without logger
        error_info = handle_exception(exc, logger=None, reraise=False)
        assert error_info["error_code"] == "EWS001"
    
    @patch('exceptions.get_timestamp')
    def test_handle_exception_timestamp(self, mock_timestamp):
        """Test exception handling timestamp generation."""
        mock_timestamp.return_value = "2025-08-27T00:00:00.000000Z"
        exc = NetworkException("Test error")
        
        error_info = handle_exception(exc, logger=None, reraise=False)
        
        assert error_info["timestamp"] == "2025-08-27T00:00:00.000000Z"
        mock_timestamp.assert_called_once()


class TestExceptionInheritance:
    """Test exception inheritance and polymorphism."""
    
    def test_all_exceptions_inherit_ews(self):
        """Test that all custom exceptions inherit from EWSException."""
        exceptions_to_test = [
            NetworkException, RenderException, SelectorException,
            ValidationException, RobotsException, RateLimitException
        ]
        
        for exc_class in exceptions_to_test:
            exc = exc_class("Test message")
            assert isinstance(exc, EWSException)
            assert isinstance(exc, Exception)
    
    def test_exception_polymorphism(self):
        """Test exception polymorphism."""
        exceptions = [
            NetworkException("Network error"),
            ValidationException("Validation error"),
            RobotsException("Robots error")
        ]
        
        # All should be catchable as EWSException
        for exc in exceptions:
            try:
                raise exc
            except EWSException as e:
                assert hasattr(e, 'code')
                assert hasattr(e, 'message')
                assert hasattr(e, 'to_dict')


class TestExceptionContextHandling:
    """Test context data handling in exceptions."""
    
    def test_context_merging(self):
        """Test context data merging in exceptions."""
        base_context = {"base": "data"}
        exc = NetworkException(
            "Test error",
            context=base_context,
            status_code=500
        )
        
        # Should merge provided context with auto-generated context
        assert exc.context["base"] == "data"
        assert exc.context["status_code"] == 500
        assert exc.context["error_type"] == "network_error"
    
    def test_context_override_protection(self):
        """Test that auto-context doesn't override explicit context."""
        exc = NetworkException(
            "Test error",
            context={"error_type": "custom_type"},
            status_code=500
        )
        
        # Explicit context should be preserved
        assert exc.context["error_type"] == "custom_type"
        assert exc.context["status_code"] == 500