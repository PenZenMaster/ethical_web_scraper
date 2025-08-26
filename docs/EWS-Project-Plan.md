# Ethical Web Scraper – Specifications (v1.0)

## 📌 Purpose
To extract specific, permitted sections of a partner website's rendered HTML (such as product details) and output the data into a JSON format suitable for republishing in WordPress or another CMS, preserving all images and links.

## 🚀 Quick Start Guide

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd ethical_web_scraper
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### First Scrape
```bash
python main.py --url "https://example.com/product" --selector ".product-detail" --output "product.json"
```

### Common Use Cases

#### Single Page Scrape
```python
from scraper import EthicalScraper

scraper = EthicalScraper()
result = scraper.scrape_url("https://example.com", ".content")
```

#### Batch Processing
```python
urls = ["https://example.com/page1", "https://example.com/page2"]
results = scraper.batch_scrape(urls, ".product-info")
```

---

## 🧩 Functional Requirements

### ✅ Must-Have
| Feature | Description |
|--------|-------------|
| Input URL | Accept a full product/detail page URL |
| Render JavaScript | Use a headless browser to load the full DOM |
| Section Targeting | Extract specific HTML node(s) by CSS selector or XPath |
| Image Preservation | Retain all image links (convert relative to absolute) |
| JSON Output | Store structured content in clean, readable JSON |
| Configurable Delay | Set crawl delay to avoid hammering partner sites |
| Slugify Filenames | Automatically generate safe file names from page title or slug |

### ✳️ Nice-to-Have (for v1.1+)
- Multiple section selectors per scrape
- Handle paginated content (load more / infinite scroll)
- Automatic alt-text extraction (or fallback to filename)
- GUI wrapper for non-technical use
- Sitemap auto-crawl and batch scrape
- Markdown output (for optional headless CMS)

---

## 🧰 Tech Stack & Tools

### 1. Core Language
- Python 3.11+

### 2. Rendering Engine
- Playwright (preferred: headless Chromium/Firefox)

### 3. Scraper Engine
- BeautifulSoup (HTML parsing)
- Optional: lxml (for XPath support)

### 4. Utilities
- slugify – for clean filenames
- typer – for CLI interface
- tenacity – for retry logic
- pydantic – optional for schema validation
- rich – terminal formatting

### 5. Output Format (JSON)
```json
{
  "title": "Insulated Garage Doors – Thermacore",
  "slug": "insulated-garage-doors-thermacore",
  "source_url": "https://...",
  "content_html": "<div class='product-detail'>...</div>",
  "images": [
    "https://...img1.jpg",
    "https://...img2.jpg"
  ],
  "scraped_at": "2025-08-25T16:20:00Z"
}
```

---

## 📂 Directory Structure (v1.0 CLI)
```
ethical_web_scraper/
├── main.py
├── scraper.py
├── browser.py
├── exporter.py
├── utils.py
├── config/
│   └── default.yaml
├── output/
├── logs/
├── requirements.txt
└── README.md
```

---

## 📋 API Documentation

### Core Classes

#### EthicalScraper
```python
class EthicalScraper:
    def __init__(self, config_path: str = "config/default.yaml")
    def scrape_url(self, url: str, selector: str, **kwargs) -> ScrapedContent
    def batch_scrape(self, urls: List[str], selector: str) -> List[ScrapedContent]
    def validate_robots_txt(self, url: str) -> bool
```

#### ScrapedContent
```python
@dataclass
class ScrapedContent:
    title: str
    slug: str
    source_url: str
    content_html: str
    images: List[str]
    scraped_at: datetime
    metadata: Dict[str, Any]
```

### Browser Module
```python
class BrowserManager:
    async def get_page(self, url: str, wait_for: str = None) -> Page
    async def render_content(self, page: Page, timeout: int = 30000) -> str
    async def close(self) -> None
```

### Exporter Module
```python
class ContentExporter:
    def export_json(self, content: ScrapedContent, filepath: str) -> None
    def export_csv(self, contents: List[ScrapedContent], filepath: str) -> None
    def validate_output(self, content: ScrapedContent) -> ValidationResult
```

---

## ⚠️ Error Handling Strategy

### Error Codes
| Code | Type | Description | Recovery Action |
|------|------|-------------|-----------------|
| EWS001 | NetworkError | Connection timeout/failure | Retry with exponential backoff |
| EWS002 | RenderError | JavaScript rendering failed | Fallback to basic HTML parsing |
| EWS003 | SelectorError | CSS selector not found | Log warning, return empty content |
| EWS004 | ValidationError | Output validation failed | Skip item, continue processing |
| EWS005 | RobotsError | Robots.txt violation | Abort with user notification |

### Exception Hierarchy
```python
class EWSException(Exception):
    """Base exception for all EWS errors"""
    def __init__(self, code: str, message: str, url: str = None)

class NetworkException(EWSException):
    """Network-related errors (EWS001)"""

class RenderException(EWSException):
    """Browser rendering errors (EWS002)"""

class SelectorException(EWSException):
    """CSS/XPath selector errors (EWS003)"""
```

### Retry Logic
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((NetworkException, RenderException))
)
def scrape_with_retry(self, url: str) -> ScrapedContent:
    # Implementation
```

---

## 📊 Configuration Schema

### default.yaml Structure
```yaml
# Browser Configuration
browser:
  headless: true
  timeout: 30000
  viewport:
    width: 1920
    height: 1080
  user_agent: "EthicalScraper/1.0 (+your-contact@example.com)"

# Scraping Behavior
scraping:
  respect_robots: true
  delay_between_requests: 2.0
  max_concurrent_requests: 3
  retry_attempts: 3
  retry_delay: 5.0

# Output Settings
output:
  format: "json"  # json, csv, xml
  pretty_print: true
  include_metadata: true
  image_handling: "absolute_urls"  # absolute_urls, download_local, base64

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/scraper.log"
  max_size_mb: 10
  backup_count: 5

# Validation Rules
validation:
  min_content_length: 100
  max_content_length: 1048576  # 1MB
  required_fields: ["title", "content_html"]
  image_url_validation: true
```

### Environment Variables
```bash
EWS_CONFIG_PATH=config/production.yaml
EWS_LOG_LEVEL=DEBUG
EWS_OUTPUT_DIR=output/
EWS_MAX_WORKERS=5
```

---

## 🧪 Testing Strategy

### Unit Tests
```bash
pytest tests/unit/ -v --cov=src --cov-report=html
```

### Integration Tests
```bash
pytest tests/integration/ -v --slow
```

### Test Categories
- **Unit Tests**: Individual function testing
- **Integration Tests**: Browser automation workflows  
- **End-to-End Tests**: Complete scraping scenarios
- **Performance Tests**: Load testing with multiple URLs
- **Security Tests**: Input validation and sanitization

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run tests
        run: pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 🔗 Module Dependencies

### Dependency Graph
```
main.py
├── scraper.py
│   ├── browser.py
│   │   └── playwright
│   ├── utils.py
│   └── exporter.py
└── config/
    └── default.yaml
```

### External Dependencies
| Package | Version | Purpose | Alternative |
|---------|---------|---------|-------------|
| playwright | ^1.40.0 | Browser automation | selenium |
| beautifulsoup4 | ^4.12.0 | HTML parsing | lxml |
| pydantic | ^2.5.0 | Data validation | dataclasses |
| typer | ^0.9.0 | CLI interface | click |
| tenacity | ^8.2.0 | Retry logic | backoff |
| rich | ^13.7.0 | Terminal output | colorama |
| pyyaml | ^6.0.1 | Configuration | toml |

### Performance Requirements
- **Memory Usage**: < 500MB per concurrent scrape
- **Response Time**: < 30s per page (including JS rendering)
- **Concurrent Requests**: Max 5 (configurable)
- **Storage**: 1MB per scraped page (average)

---

## ⚖️ Ethical Considerations
- Only scrape with permission
- Respect `robots.txt` by default (toggleable)
- Identify scraper via user-agent: `EthicalScraper/1.0 (+contact info)`
- Implement rate limiting to avoid server overload
- Provide opt-out mechanisms for site owners

---

## 🔄 Resilience & Logging

### Logging Levels
- **DEBUG**: Detailed execution flow, variable states
- **INFO**: Successful operations, configuration loaded
- **WARNING**: Recoverable errors, fallback actions
- **ERROR**: Failed operations, validation errors
- **CRITICAL**: System failures, security violations

### Log Format
```
2025-08-26 10:15:30 | INFO | scraper.py:45 | Successfully scraped https://example.com
2025-08-26 10:15:31 | ERROR | browser.py:123 | EWS002: Failed to render JS content for https://example.com
```

### Monitoring & Alerts
- Failed scrape rate > 10%
- Memory usage > 1GB  
- Response time > 60s
- Robots.txt violations

---

## 📥 WordPress Import Prep
- Clean HTML string in JSON
- Option to strip container div
- Absolute image URLs

---

## 🛠️ Troubleshooting

### Common Issues

#### Browser Fails to Launch
```bash
# Install browser binaries
playwright install chromium

# Check system dependencies
playwright install-deps
```

#### Selector Not Found
```python
# Use multiple fallback selectors
selectors = [".product-detail", ".content", "#main"]
for selector in selectors:
    if soup.select(selector):
        break
```

#### Memory Issues
```yaml
# Reduce concurrent requests in config
scraping:
  max_concurrent_requests: 1
  
# Enable headless mode
browser:
  headless: true
```

#### Rate Limiting
```yaml
# Increase delays
scraping:
  delay_between_requests: 5.0
  retry_delay: 10.0
```

### Debug Commands
```bash
# Run with debug logging
EWS_LOG_LEVEL=DEBUG python main.py --url "https://example.com"

# Test single component
python -m pytest tests/unit/test_browser.py -v -s

# Validate configuration
python -c "from utils import load_config; print(load_config())"
```

---

## 🧬 Future Extensibility

### Roadmap
| Version | Features | Timeline |
|---------|----------|----------|
| v1.1 | Multiple selectors, paginated content | Q4 2025 |
| v1.2 | GUI interface, screenshot logging | Q1 2026 |
| v1.3 | WordPress REST API integration | Q2 2026 |
| v2.0 | Browser extension, scheduled jobs | Q3 2026 |

### Architecture Extensions
```python
# Plugin system for custom extractors
class ExtractorPlugin:
    def extract(self, soup: BeautifulSoup, config: dict) -> dict:
        pass

# Webhook notifications
class NotificationHandler:
    def on_scrape_complete(self, result: ScrapedContent):
        pass
    def on_error(self, error: EWSException):
        pass
```

---

## 📝 Contributing Guidelines

### Development Setup
```bash
git clone <repository-url>
cd ethical_web_scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

### Code Standards
- **Style**: Black formatter, isort imports
- **Type Hints**: Required for all public methods
- **Docstrings**: Google style for classes and functions
- **Testing**: 90%+ coverage requirement
- **Security**: No hardcoded secrets, input validation

### Pull Request Process
1. Create feature branch from `main`
2. Add tests for new functionality  
3. Update documentation if needed
4. Run full test suite: `pytest`
5. Submit PR with clear description

### Commit Conventions
```
feat: add batch processing support
fix: handle empty selector results
docs: update API documentation
test: add integration tests for browser module
refactor: simplify error handling logic
```

---

## ✅ Project Status Checklist
- [x] Use Case: OHD Joliet scraping from OHD.com
- [x] Target selector: `.product-detail[product-detail]`
- [x] Format: HTML section + image links in JSON
- [x] Tools chosen: Playwright + BeautifulSoup
- [x] API documentation completed
- [x] Error handling strategy defined
- [x] Configuration schema documented
- [x] Testing strategy outlined
- [ ] Implementation phase ready to begin

---