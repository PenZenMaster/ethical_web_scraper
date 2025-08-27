# Ethical Web Scraper

A production-ready web scraping tool designed for ethical content migration and extraction. Features Playwright-powered JavaScript rendering, WordPress migration support, and comprehensive export formats.

## 🎯 Key Features

- **JavaScript-Rendered Scraping**: Full Playwright browser automation with dynamic content support
- **WordPress Migration**: Native WordPress XML export for seamless content migration
- **Image Management**: Download, organize, and rehost images with multiple handling modes
- **Multi-Format Export**: JSON, CSV, XML, and WordPress XML formats
- **Ethical Compliance**: Built-in robots.txt validation and rate limiting
- **Batch Processing**: Handle multiple URLs with progress tracking and error recovery
- **CSS Selector Targeting**: Precise content extraction with fallback selectors
- **Production Ready**: Comprehensive error handling, logging, and validation

## 🚀 Quick Start

### Option 1: Use Convenience Scripts (Recommended)
```bash
# General scraping
./run.bat scrape "https://example.com" --selector "article"

# WordPress migration  
./wp-migrate.bat wordpress_urls.txt my_migration
```

### Option 2: Direct Commands
```bash
# Single URL scraping
python main.py scrape "https://example.com" --selector "body" --format json

# WordPress migration
python main.py wordpress urls.txt --output "wp_import"

# Batch processing
python main.py batch urls.txt --format csv --output-dir results
```

## 📋 Command Reference

### Core Commands

**`scrape`** - Extract content from a single URL
```bash
python main.py scrape "https://example.com" [OPTIONS]

Options:
  -s, --selector TEXT    CSS selector for content extraction [default: body]
  -o, --output TEXT      Output filename (without extension) 
  -f, --format TEXT      Export format: json, csv, xml, all [default: json]
  -c, --config TEXT      Path to configuration file
  --robots/--no-robots   Respect robots.txt [default: robots]
  --headless/--no-headless  Run browser in headless mode [default: headless]
  -v, --verbose          Enable verbose logging
```

**`batch`** - Process multiple URLs from file
```bash
python main.py batch urls.txt [OPTIONS]

Options:
  -d, --output-dir TEXT  Output directory [default: output]
  -s, --selector TEXT    CSS selector [default: body]  
  -f, --format TEXT      Export format: json, csv, xml [default: json]
  -c, --config TEXT      Configuration file path
  --robots/--no-robots   Respect robots.txt [default: robots]
  -v, --verbose          Enable verbose logging
```

**`wordpress`** - WordPress content migration
```bash
python main.py wordpress urls.txt [OPTIONS]

Options:
  -o, --output TEXT      Output filename [default: wordpress_import]
  -c, --config TEXT      WordPress config [default: config/wordpress.yaml]  
  -s, --selector TEXT    CSS selector (auto = WordPress detection) [default: auto]
  -v, --verbose          Enable verbose logging
```

**`test`** - Quick functionality test
```bash
python main.py test
```

### WordPress Migration Workflow

1. **Create URLs file:**
   ```
   https://source-wp-site.com/post-1/
   https://source-wp-site.com/post-2/
   # Comments are ignored
   ```

2. **Run migration:**
   ```bash
   python main.py wordpress my_urls.txt --output "site_migration"
   ```

3. **Import to WordPress:**
   - Go to WordPress Admin → Tools → Import → WordPress
   - Upload the generated `site_migration.xml`
   - Review and import content (imported as drafts)

## 🛠️ Setup & Installation

### Standard Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies (core packages work without venv issues)
pip install playwright beautifulsoup4 typer rich PyYAML tenacity

# Install Playwright browsers
playwright install
```

### Alternative: System Packages
If you encounter venv issues, the application works with system-wide packages:
```bash
python main.py --help
```

## 📁 Project Structure

```
ethical_web_scraper/
├── main.py              # CLI interface
├── scraper.py           # Core scraping engine
├── exporter.py          # Multi-format export system
├── browser.py           # Playwright browser management
├── utils.py             # Configuration and utilities
├── exceptions.py        # Structured error handling
├── run.bat             # Convenience script
├── wp-migrate.bat      # WordPress migration script
├── config/
│   ├── default.yaml    # Standard configuration
│   └── wordpress.yaml  # WordPress-specific settings
├── logs/               # Application logs
├── output/             # Default export directory
└── tests/              # Comprehensive test suite (107 tests)
```

## 🎛️ Configuration

### Default Configuration (`config/default.yaml`)
- Standard scraping settings
- General export options
- Basic ethical compliance

### WordPress Configuration (`config/wordpress.yaml`)
- WordPress-specific selectors and timeouts  
- Migration-optimized settings
- Content filtering for clean imports
- Image downloading and rehosting for migration

### Image Management Settings
Available in both configurations:
```yaml
image_settings:
  download_directory: "images"        # Local download directory
  organize_by_domain: true           # Organize by source domain
  max_image_size: "5MB"             # Maximum file size
  allowed_formats: ["jpg", "png"]    # Allowed image formats
  optimize: false                    # Image optimization
  quality: 85                        # JPEG quality (1-100)
  wordpress_upload: false            # WordPress media integration
```

**Image Handling Modes**:
- `absolute_urls`: Convert relative URLs to absolute (default)
- `download_local`: Download images to local directory
- `download_and_rehost`: Download for rehosting (WordPress mode)
- `base64`: Embed small images as base64 (planned)

### Custom Configuration
```bash
python main.py scrape "url" --config "path/to/custom.yaml"
```

## ✅ Production Features

### Ethical Compliance
- **Robots.txt Validation**: Automatic compliance checking
- **Rate Limiting**: Configurable requests per domain per minute
- **User-Agent Identification**: Clear identification in requests
- **Recovery Suggestions**: Helpful error messages with next steps

### Error Handling
- **Structured Error Codes**: EWS001-EWS006 with context
- **Graceful Degradation**: Continues processing on individual failures
- **Comprehensive Logging**: Detailed logs for debugging
- **Retry Logic**: Automatic retries with exponential backoff

### Content Validation
- **Length Validation**: Configurable minimum/maximum content length
- **Required Fields**: Ensures essential data is present
- **Schema Validation**: Export format compliance checking
- **Image Handling**: Automatic image URL processing

## 🧪 Testing

Run the comprehensive test suite:
```bash
pytest
# 107 tests covering all major functionality
```

Quick functionality test:
```bash
python main.py test
```

## 📊 Export Formats

### JSON (Default)
Structured data with metadata, images, and content.

### CSV  
Tabular format for spreadsheet analysis and bulk operations.

### XML
Generic XML structure for custom integrations.

### WordPress XML
Native WordPress export format for direct import via WordPress admin.

## 📈 Performance

- **Average Speed**: ~7-8 seconds per URL
- **Success Rate**: 100% for accessible content
- **Memory Efficient**: Automatic browser cleanup
- **Concurrent Support**: Built for future scaling

## 🆘 Troubleshooting

### Virtual Environment Issues
```bash
# If venv creation fails, use --without-pip
python -m venv .venv --without-pip
.venv\Scripts\python.exe -m ensurepip --upgrade
```

### Missing Dependencies  
```bash
# Install core packages individually
pip install playwright beautifulsoup4 typer rich PyYAML
```

### Permission Errors
```bash
# Use convenience scripts
./run.bat --help
./wp-migrate.bat
```

## 📝 Examples

### Basic Content Extraction
```bash
python main.py scrape "https://example.com" --selector "article" --output "content"
```

### Batch WordPress Migration
```bash
# Create urls.txt with WordPress post URLs
python main.py wordpress urls.txt --output "blog_migration"
```

### Multi-Format Export
```bash
python main.py scrape "https://example.com" --format all
# Exports JSON, CSV, and XML versions
```

### Custom Configuration
```bash
python main.py scrape "url" --config "config/wordpress.yaml" --verbose
```

**Status: Production Ready** 🚀  
Current Version: Sprint 1.2 Complete  
Test Coverage: 107 comprehensive unit tests