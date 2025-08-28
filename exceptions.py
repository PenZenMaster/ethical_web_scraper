"""
Module/Script Name: exceptions.py
Path: ethical_web_scraper/exceptions.py

Description:
Centralized exception hierarchy and error codes for the Ethical Web Scraper project.
Implements the complete EWS error code system (EWS001-EWS005) with structured
error handling and recovery strategies.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-27

Comments:
* v1.00 - Initial implementation of complete EWS exception hierarchy
"""

from typing import Optional, Dict, Any
from datetime import datetime

# Import for test compatibility
try:
    from utils import get_timestamp
except ImportError:
    def get_timestamp() -> str:
        return datetime.utcnow().isoformat() + 'Z'


class EWSException(Exception):
    """
    Base exception for all Ethical Web Scraper errors.
    
    Provides structured error information including error codes,
    recovery suggestions, and contextual data.
    """
    
    def __init__(
        self, 
        code: str, 
        message: str, 
        url: Optional[str] = None,
        recovery_action: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize EWS exception.
        
        Args:
            code: Error code (EWS001-EWS005)
            message: Human-readable error message
            url: URL associated with the error (if applicable)
            recovery_action: Suggested recovery action
            context: Additional context information
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.url = url
        self.recovery_action = recovery_action
        self.context = context or {}
        self.timestamp = get_timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for logging/serialization.
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            'error_code': self.code,
            'message': self.message,
            'url': self.url,
            'recovery_action': self.recovery_action,
            'context': self.context,
            'timestamp': self.timestamp,
            'exception_type': self.__class__.__name__
        }
    
    def __str__(self) -> str:
        """String representation with error code."""
        url_part = f" (URL: {self.url})" if self.url else ""
        return f"{self.code}: {self.message}{url_part}"


class NetworkException(EWSException):
    """
    Network-related errors (EWS001).
    
    Covers connection timeouts, DNS failures, HTTP errors,
    and other network-level issues.
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        retry_count: int = 0,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize network exception.
        
        Args:
            message: Error message
            url: URL that failed
            status_code: HTTP status code (if applicable)
            retry_count: Number of retry attempts made
            context: Additional context
        """
        recovery_action = "Check network connectivity and retry with exponential backoff"
        if status_code and status_code >= 500:
            recovery_action = "Server error - retry later"
        elif status_code and status_code == 429:
            recovery_action = "Rate limited - increase delay between requests"
        elif status_code and status_code in [403, 401]:
            recovery_action = "Check user-agent and access permissions"
        
        context = context or {}
        if status_code:
            context['status_code'] = status_code
        # Set error_type only if not already provided in context
        if 'error_type' not in context:
            if status_code and status_code < 500:
                context['error_type'] = 'http_error'
            else:
                context['error_type'] = 'network_error'
        context['retry_count'] = retry_count
        
        super().__init__(
            code="EWS001",
            message=message,
            url=url,
            recovery_action=recovery_action,
            context=context
        )
        self.status_code = status_code
        self.retry_count = retry_count


class RenderException(EWSException):
    """
    JavaScript rendering errors (EWS002).
    
    Covers browser startup failures, page rendering issues,
    JavaScript execution problems, and timeout errors.
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        browser_error: Optional[str] = None,
        timeout: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize render exception.
        
        Args:
            message: Error message
            url: URL being rendered
            browser_error: Underlying browser error
            timeout: Timeout value if applicable
            context: Additional context
        """
        recovery_action = "Fallback to basic HTML parsing for page loading issues"
        if "timeout" in message.lower():
            recovery_action = "Increase browser timeout or retry page loading"
        elif "browser" in message.lower():
            recovery_action = "Restart browser or use different browser engine"
        
        context = context or {}
        if browser_error:
            context['browser_error'] = browser_error
        if timeout:
            context['timeout'] = timeout
        
        super().__init__(
            code="EWS002",
            message=message,
            url=url,
            recovery_action=recovery_action,
            context=context
        )
        self.browser_error = browser_error


class SelectorException(EWSException):
    """
    CSS/XPath selector errors (EWS003).
    
    Covers selector not found, invalid selector syntax,
    and content extraction failures.
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        selector: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize selector exception.
        
        Args:
            message: Error message
            url: URL where selector failed
            selector: CSS selector that failed
            context: Additional context
        """
        recovery_action = "Log warning, return empty content"
        if selector:
            recovery_action = f"Try fallback selectors or verify '{selector}' exists"
        
        context = context or {}
        if selector:
            context['selector'] = selector
        
        super().__init__(
            code="EWS003",
            message=message,
            url=url,
            recovery_action=recovery_action,
            context=context
        )
        self.selector = selector


class ValidationException(EWSException):
    """
    Output validation errors (EWS004).
    
    Covers content validation failures, schema validation,
    and data quality issues.
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        validation_type: Optional[str] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None,
        recovery_action: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation exception.
        
        Args:
            message: Error message
            url: URL of content that failed validation
            validation_type: Type of validation that failed
            expected_value: Expected value
            actual_value: Actual value that failed
            context: Additional context
        """
        if recovery_action is None:
            recovery_action = "Skip item, continue processing"
            if validation_type == "content_length":
                recovery_action = "Adjust content length limits or use different selector"
            elif validation_type == "required_field":
                recovery_action = "Provide default value or make field optional"
        
        context = context or {}
        if validation_type:
            context['validation_type'] = validation_type
        if expected_value is not None:
            context['expected_value'] = expected_value
        if actual_value is not None:
            context['actual_value'] = actual_value
        
        super().__init__(
            code="EWS004",
            message=message,
            url=url,
            recovery_action=recovery_action,
            context=context
        )
        self.validation_type = validation_type
        self.expected_value = expected_value
        self.actual_value = actual_value


class RobotsException(EWSException):
    """
    Robots.txt violation errors (EWS005).
    
    Covers robots.txt parsing failures and access violations.
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        robots_url: Optional[str] = None,
        user_agent: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize robots exception.
        
        Args:
            message: Error message
            url: URL that violated robots.txt
            robots_url: URL of robots.txt file
            user_agent: User agent string used
            context: Additional context
        """
        recovery_action = "Abort with user notification"
        if "disallows" in message.lower():
            recovery_action = "Respect robots.txt - skip URL or change user-agent"
        
        context = context or {}
        if robots_url:
            context['robots_url'] = robots_url
        if user_agent:
            context['user_agent'] = user_agent
        
        super().__init__(
            code="EWS005",
            message=message,
            url=url,
            recovery_action=recovery_action,
            context=context
        )
        self.robots_url = robots_url
        self.user_agent = user_agent


class ConfigurationError(EWSException):
    """
    Configuration loading and validation errors.
    
    Not part of the main EWS001-005 codes but used for
    system-level configuration issues.
    """
    
    def __init__(
        self, 
        message: str, 
        config_path: Optional[str] = None,
        section: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration exception.
        
        Args:
            message: Error message
            config_path: Path to configuration file
            section: Configuration section that failed
            context: Additional context
        """
        recovery_action = "Check configuration file and fix errors"
        
        context = context or {}
        if config_path:
            context['config_path'] = config_path
        if section:
            context['section'] = section
        
        super().__init__(
            code="EWS_CONFIG",
            message=message,
            recovery_action=recovery_action,
            context=context
        )
        self.config_path = config_path
        self.section = section


class RateLimitException(EWSException):
    """
    Rate limiting errors (EWS006).
    
    Used when domain-level or request-level rate limits
    are exceeded to prevent overwhelming servers.
    """
    
    def __init__(self, message: str, domain: Optional[str] = None, current_rate: Optional[int] = None, **kwargs):
        context = kwargs.pop('context', {})
        context.update({
            'domain': domain,
            'current_rate': current_rate,
            'error_type': 'rate_limit_exceeded'
        })
        
        super().__init__(
            code="EWS006",
            message=message,
            recovery_action="Wait before making additional requests or reduce scraping frequency",
            context=context,
            **kwargs
        )
        self.domain = domain
        self.current_rate = current_rate


# Exception mapping for error code lookup
ERROR_CODE_MAP = {
    "EWS001": NetworkException,
    "EWS002": RenderException,
    "EWS003": SelectorException,
    "EWS004": ValidationException,
    "EWS005": RobotsException,
    "EWS006": RateLimitException,
    "EWS_CONFIG": ConfigurationError
}


def create_exception_from_code(
    error_code: str, 
    message: str, 
    **kwargs
) -> EWSException:
    """
    Create an exception instance from error code.
    
    Args:
        error_code: EWS error code
        message: Error message
        **kwargs: Additional arguments for specific exception types
        
    Returns:
        Appropriate exception instance
        
    Raises:
        ValueError: If error code is not recognized
    """
    if error_code not in ERROR_CODE_MAP:
        # Create a generic EWSException for unknown error codes
        return EWSException(
            code=error_code,
            message=message,
            recovery_action="Check error code documentation",
            **kwargs
        )
    
    exception_class = ERROR_CODE_MAP[error_code]
    return exception_class(message, **kwargs)


def handle_exception(
    exception, 
    logger=None, 
    reraise: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Centralized exception handling with logging and recovery suggestions.
    
    Args:
        exception: Exception to handle (EWS or standard)
        logger: Logger instance for error reporting
        reraise: Whether to re-raise the exception after handling
        
    Returns:
        Exception information dictionary if not re-raising
        
    Raises:
        Exception: Re-raises the original exception if reraise=True
    """
    if isinstance(exception, EWSException):
        # Handle EWS exceptions
        error_info = exception.to_dict()
        
        if logger:
            logger.error(
                f"EWS Error {exception.code}: {exception.message}",
                extra={'error_details': error_info}
            )
            
            if exception.recovery_action:
                logger.info(f"Recovery suggestion: {exception.recovery_action}")
    else:
        # Handle non-EWS exceptions
        error_info = {
            'error_code': 'UNKNOWN',
            'exception_type': type(exception).__name__,
            'message': str(exception),
            'timestamp': get_timestamp()
        }
        
        if logger:
            logger.error(
                f"Unexpected error ({type(exception).__name__}): {exception}"
            )
    
    if reraise:
        raise exception
    
    return error_info