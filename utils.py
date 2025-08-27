"""
Module/Script Name: utils.py
Path: ethical_web_scraper/utils.py

Description:
Utility functions for configuration loading, logging setup, and content processing
for the Ethical Web Scraper project.

Author(s):
Rank Rocket Co (C) Copyright 2025 - All Rights Reserved

Created Date:
2025-08-27

Last Modified Date:
2025-08-27

Comments:
* v1.00 - Initial implementation with configuration loading and logging setup
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import yaml
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from slugify import slugify

# Import centralized exceptions
from exceptions import ConfigurationError


def load_config(config_path: str = "config/default.yaml") -> Dict[str, Any]:
    """
    Load and validate configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict containing configuration data
        
    Raises:
        ConfigurationError: If config file not found or invalid
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate required configuration sections
        required_sections = ['browser', 'scraping', 'output', 'logging']
        for section in required_sections:
            if section not in config:
                raise ConfigurationError(f"Missing required configuration section: {section}")
        
        # Set defaults for optional values
        config.setdefault('scraping', {}).setdefault('delay_between_requests', 2.0)
        config.setdefault('browser', {}).setdefault('headless', True)
        config.setdefault('output', {}).setdefault('format', 'json')
        
        return config
        
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML configuration: {e}")
    except Exception as e:
        raise ConfigurationError(f"Error loading configuration: {e}")


def setup_logging(config: Dict[str, Any] = None, log_dir: str = "logs") -> logging.Logger:
    """
    Configure structured logging for the application.
    
    Args:
        config: Configuration dictionary with logging settings
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)
    
    # Default logging configuration
    if config is None:
        config = {
            'logging': {
                'level': 'INFO',
                'file': 'logs/scraper.log',
                'max_size_mb': 10,
                'backup_count': 5
            }
        }
    
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    log_file = log_config.get('file', 'logs/scraper.log')
    max_size = log_config.get('max_size_mb', 10) * 1024 * 1024  # Convert to bytes
    backup_count = log_config.get('backup_count', 5)
    
    # Create logger
    logger = logging.getLogger('ethical_web_scraper')
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_size, backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized - Level: {log_config.get('level', 'INFO')}, File: {log_file}")
    return logger


def get_environment_config() -> Dict[str, Any]:
    """
    Get configuration overrides from environment variables.
    
    Returns:
        Dict containing environment variable overrides
    """
    env_config = {}
    
    # Map environment variables to config paths
    env_mappings = {
        'EWS_LOG_LEVEL': ('logging', 'level'),
        'EWS_OUTPUT_DIR': ('output', 'directory'),
        'EWS_MAX_WORKERS': ('scraping', 'max_concurrent_requests'),
        'EWS_DELAY': ('scraping', 'delay_between_requests'),
        'EWS_HEADLESS': ('browser', 'headless')
    }
    
    for env_var, (section, key) in env_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            if section not in env_config:
                env_config[section] = {}
            
            # Type conversion
            if key in ['max_concurrent_requests', 'timeout']:
                env_config[section][key] = int(value)
            elif key in ['delay_between_requests']:
                env_config[section][key] = float(value)
            elif key in ['headless']:
                env_config[section][key] = value.lower() in ('true', '1', 'yes')
            else:
                env_config[section][key] = value
    
    return env_config


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge configuration dictionaries with override taking precedence.
    
    Args:
        base_config: Base configuration dictionary
        override_config: Override configuration dictionary
        
    Returns:
        Merged configuration dictionary
    """
    merged = base_config.copy()
    
    for section, values in override_config.items():
        if section in merged and isinstance(merged[section], dict) and isinstance(values, dict):
            merged[section].update(values)
        else:
            merged[section] = values
    
    return merged


def extract_content(html: str, selector: str, base_url: str = "") -> tuple[str, List[str]]:
    """
    Extract content from HTML using CSS selector and process images.
    
    Args:
        html: HTML content to parse
        selector: CSS selector for content extraction
        base_url: Base URL for resolving relative image URLs
        
    Returns:
        Tuple of (content_html, image_urls)
        
    Raises:
        ValueError: If selector not found in HTML
    """
    soup = BeautifulSoup(html, "lxml")
    section = soup.select_one(selector)
    if not section:
        raise ValueError(f"No element found for selector: {selector}")
    
    images = []
    # Find all img tags - they should be Tag elements
    for img_element in section.find_all("img"):
        # Ensure we're working with a Tag element (not NavigableString)
        if isinstance(img_element, Tag):
            # Use attrs dictionary directly for type safety
            src_value = img_element.attrs.get("src")
            if src_value:
                # Handle case where src might be a list (though rare)
                src = src_value[0] if isinstance(src_value, list) else src_value
                if isinstance(src, str):
                    abs_src = urljoin(base_url, src) if base_url else src
                    images.append(abs_src)
                    # Set the absolute URL back to the element
                    img_element.attrs["src"] = abs_src

    return str(section), images


def get_slug_from_title(title: str) -> str:
    """
    Generate URL-safe slug from title.
    
    Args:
        title: Original title string
        
    Returns:
        Slugified version of title
    """
    return slugify(title.strip().lower())


def validate_url(url: str) -> bool:
    """
    Basic URL validation.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL appears valid
    """
    return url.startswith(('http://', 'https://')) and '.' in url


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        ISO format timestamp string
    """
    return datetime.utcnow().isoformat() + 'Z'