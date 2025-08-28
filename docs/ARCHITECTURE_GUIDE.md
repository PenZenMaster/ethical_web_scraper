# Architecture Guide - Ethical Web Scraper v1.1

## Overview

The Ethical Web Scraper v1.1 implements a modular architecture with clear separation of concerns. This guide explains the system design, component relationships, and how to extend the framework.

## Core Architecture Principles

### 1. Modular Design
- **Single Responsibility**: Each module handles one specific concern
- **Loose Coupling**: Components communicate through well-defined interfaces  
- **High Cohesion**: Related functionality grouped together
- **Extensibility**: Easy to add new validators, exporters, and processors

### 2. Configuration-Driven Behavior
- YAML-based configuration system
- Environment-specific configs (default, wordpress, testing)
- Runtime configuration validation
- Hot-swappable components based on config

### 3. Async/Await Pattern
- Non-blocking I/O operations
- Concurrent request processing with rate limiting
- Efficient resource utilization
- Graceful error handling

## System Components

### Core Application Layer

```
ethical_web_scraper/
├── main.py              # CLI entry point
├── scraper.py           # Main scraping orchestrator  
├── browser_manager.py   # Playwright browser management
├── exceptions.py        # Custom exception hierarchy
└── config/              # Configuration files
```

**Key Responsibilities:**
- CLI command processing (Typer framework)
- Browser lifecycle management
- High-level scraping workflow coordination
- Error handling and recovery

### Validation Layer (`validators/`)

```
validators/
├── __init__.py          # Package exports
├── base_validator.py    # Abstract base class
├── url_validator.py     # URL format and accessibility validation
├── robots_validator.py  # robots.txt compliance checking  
├── content_validator.py # Content quality and requirements validation
└── config_validator.py  # Configuration file validation
```

**Architecture Pattern:**
```python
class BaseValidator(ABC):
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    @abstractmethod
    def validate(self, *args, **kwargs) -> bool:
        pass
    
    def get_error_message(self) -> str:
        return getattr(self, '_error_message', 'Validation failed')
```

**Usage Pattern:**
```python
# Initialize validators
url_validator = URLValidator(config, logger)
robots_validator = RobotsValidator(config, logger)

# Chain validation
if url_validator.validate(url) and robots_validator.validate(url):
    proceed_with_scraping()
```

### Rate Limiting Layer (`rate_limiting/`)

```
rate_limiting/
├── __init__.py          # Package exports  
├── base_limiter.py      # Abstract rate limiter
├── domain_limiter.py    # Per-domain rate limiting
└── token_bucket.py      # Token bucket algorithm implementation
```

**Key Features:**
- Domain-based rate limiting
- Configurable requests per minute
- Token bucket algorithm for burst handling
- Async-compatible with minimal blocking

### Image Processing Layer (`image_processing/`)

```
image_processing/
├── __init__.py          # Package exports
├── base_processor.py    # Abstract image processor
├── image_downloader.py  # HTTP image downloading
├── image_optimizer.py   # Compression and optimization
└── image_storage.py     # File system storage management
```

**Processing Pipeline:**
```python
# Image processing workflow
image_manager = ImageManager(config, logger)
processed_images = await image_manager.process_images(
    content_html, 
    source_url, 
    mode='download_and_rehost'
)
```

### Export Layer (`exporters/`)

```
exporters/
├── __init__.py          # Package exports
├── base_exporter.py     # Abstract exporter interface
├── json_exporter.py     # JSON format export
├── xml_exporter.py      # Generic XML export
├── csv_exporter.py      # CSV/spreadsheet export
└── wordpress_exporter.py # WordPress XML format
```

**Factory Pattern Implementation:**
```python
class ExporterFactory:
    @staticmethod
    def create_exporter(format_type: str, config: dict, logger) -> BaseExporter:
        exporters = {
            'json': JsonExporter,
            'xml': XmlExporter,
            'csv': CsvExporter,
            'wordpress_xml': WordPressExporter
        }
        return exporters[format_type](config, logger)
```

## Data Flow Architecture

### 1. Request Processing Flow

```
CLI Input → Configuration Loading → URL Validation → 
Robots.txt Check → Rate Limiting → Browser Request → 
Content Extraction → Content Validation → Image Processing → 
Export Processing → File Output
```

### 2. Error Handling Flow

```
Exception Raised → Exception Classification → 
Log Generation → Recovery Attempt → 
User Notification → Graceful Degradation
```

### 3. Configuration Resolution

```
Default Config → Environment Config → 
User Config → CLI Overrides → Runtime Configuration
```

## Extension Points

### Adding New Validators

1. **Create validator class**:
```python
# validators/custom_validator.py
from .base_validator import BaseValidator

class CustomValidator(BaseValidator):
    def validate(self, data) -> bool:
        # Implementation
        if not self._check_custom_rules(data):
            self._error_message = "Custom validation failed"
            return False
        return True
```

2. **Register in package**:
```python
# validators/__init__.py
from .custom_validator import CustomValidator
__all__ = ['BaseValidator', 'URLValidator', 'CustomValidator']
```

3. **Use in scraper**:
```python
# scraper.py
self.custom_validator = CustomValidator(self.config, self.logger)
```

### Adding New Export Formats

1. **Implement exporter**:
```python
# exporters/custom_exporter.py  
from .base_exporter import BaseExporter

class CustomExporter(BaseExporter):
    def export(self, content, filepath=None, output_dir=None) -> str:
        # Custom format implementation
        pass
```

2. **Register in factory**:
```python
# Update ExporterFactory mapping
exporters = {
    'custom': CustomExporter,
    # ... existing exporters
}
```

### Adding New Image Processors

1. **Extend base processor**:
```python
# image_processing/custom_processor.py
from .base_processor import BaseProcessor

class CustomProcessor(BaseProcessor):
    async def process(self, image_data, options) -> ProcessedImage:
        # Custom processing logic
        pass
```

## Configuration Architecture

### Configuration Hierarchy
```yaml
# config/default.yaml - Base settings
# config/wordpress.yaml - WordPress-specific overrides  
# config/testing.yaml - Test environment settings
# user_config.yaml - User customizations
```

### Configuration Validation
```python
# Automatic validation on load
config_validator = ConfigValidator(logger)
if not config_validator.validate(loaded_config):
    raise ConfigurationException(config_validator.get_error_message())
```

## Testing Architecture

### Test Organization
```
tests/
├── unit/                # Unit tests for individual components
│   ├── test_validators/ # Validator unit tests
│   ├── test_exporters/  # Exporter unit tests  
│   └── test_processors/ # Processor unit tests
├── integration/         # Integration tests
└── fixtures/            # Test data and mocks
```

### Testing Patterns
```python
# Mock-based testing for external dependencies
@patch('scraper.browser_manager')
def test_scraping_workflow(mock_browser):
    mock_browser.get_content.return_value = test_content
    # Test implementation
```

## Performance Considerations

### Async Operations
- All I/O operations use async/await
- Concurrent processing with controlled concurrency limits
- Non-blocking rate limiting implementation

### Memory Management
- Streaming for large file operations
- Lazy loading of heavy resources
- Automatic cleanup of browser resources

### Caching Strategy
- robots.txt caching (24-hour TTL)
- DNS resolution caching
- Configuration caching with change detection

## Security Architecture

### Input Validation
- URL sanitization and validation
- File path traversal prevention
- Configuration injection protection

### Rate Limiting
- Per-domain request throttling
- Burst protection with token buckets
- Configurable ethical limits

### Data Sanitization  
- HTML content sanitization
- XSS prevention in exported data
- Safe file naming and storage

## Development Workflow

### Pre-commit Validation
```cmd
REM Automated via git hooks
python -c "import scraper, validators, exporters"  REM Import check
black . --check                                    REM Code formatting
ruff --fix .                                      REM Linting
mypy . --strict                                   REM Type checking
pytest -q                                         REM Unit tests
```

### Code Quality Standards
- Type hints on all public APIs (PEP 484)
- Google-style docstrings (PEP 257)
- 90%+ test coverage for new code
- No print statements in library code (use logging)

## Deployment Architecture

### Production Checklist
- [ ] Configuration validation passes
- [ ] All tests passing
- [ ] Import validation successful
- [ ] Performance benchmarks met
- [ ] Security scan clean
- [ ] Documentation updated

### Environment Configuration
```yaml
# Production recommendations
scraping:
  max_concurrent_requests: 5
  delay_between_requests: 2.0
  respect_robots: true

logging:
  level: 'INFO'
  file: 'logs/production.log'
  
validation:
  strict_mode: true
```

## Troubleshooting

### Common Architecture Issues

**Import Errors:**
```cmd
REM Check module structure
python -c "import validators; print(validators.__all__)"
```

**Configuration Conflicts:**
```cmd
REM Validate configuration
python -m ethical_web_scraper.config.validator config/wordpress.yaml
```

**Memory Issues:**
```cmd
REM Monitor resource usage  
python -m cProfile -o profile.stats main.py scrape [url]
```

## Migration from v1.0

### Breaking Changes
- Monolithic modules split into packages
- Import paths changed (automatic compatibility layer provided)
- Configuration schema extended (backward compatible)

### Migration Steps
1. Update import statements to use new package structure
2. Review custom validators/exporters for new base class requirements  
3. Update configuration files to use new schema
4. Run test suite to verify compatibility

## Future Architecture Plans

### v1.2 Roadmap
- Plugin system for third-party extensions
- REST API layer for programmatic access
- Distributed processing capabilities
- Enhanced caching with Redis support

### Extension Points Ready for v1.2
- Authentication providers
- Content transformation pipelines  
- Advanced scheduling systems
- Multi-format simultaneous exports

---

**Architecture Version**: v1.1.0  
**Last Updated**: 2025-08-28  
**Maintainer**: Rank Rocket Co  
**License**: All Rights Reserved