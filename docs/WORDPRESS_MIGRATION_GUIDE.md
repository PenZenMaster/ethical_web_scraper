# WordPress Migration Guide for Humans 🚀

A practical, step-by-step guide to using the Ethical Web Scraper for migrating content to WordPress.

## 🎯 What This Tool Does

The Ethical Web Scraper helps you extract content from websites and convert it into WordPress XML format, which you can then import directly into your WordPress site via the admin panel.

## 🚀 Quick Start (Most Common Use Case)

### Step 1: Create Your URLs File
Create a text file with the URLs you want to scrape, one per line:

```
https://example-site.com/post-1/
https://example-site.com/post-2/
https://example-site.com/article-about-something/
```

**⚠️ Important**: URLs should NOT have quotes around them.

### Step 2: Run the Migration
```cmd
run.bat wordpress my_urls.txt --output "my_import"
```

### Step 3: Import to WordPress
1. Go to your WordPress Admin → Tools → Import → WordPress
2. Upload the generated `my_import.xml` file
3. Review and import the content (imported as drafts)

## 📋 Complete Command Reference

### Basic WordPress Migration
```cmd
run.bat wordpress [urls_file] --output "import_name"
```

### With Custom CSS Selector
```cmd
run.bat wordpress [urls_file] --selector ".content-area" --output "import_name"
```

### WordPress Auto-Detection (Recommended)
```cmd
run.bat wordpress [urls_file] --output "import_name"
```
The tool automatically tries common WordPress selectors:
- `article.post`
- `.post-content` 
- `.entry-content`
- `#content article`
- `main article`
- `.post`

## 🎛️ CSS Selector Guide

### Understanding CSS Selectors

| HTML Element | CSS Selector | Example |
|--------------|--------------|---------|
| `<div class="content">` | `.content` | Single class (note the dot) |
| `<div id="main">` | `#main` | ID selector (note the #) |
| `<article id="post-123">` | `article#post-123` | Element with ID |
| `<div class="post main">` | `.post.main` | Multiple classes (no spaces) |
| `<div class="outer"><div class="inner">` | `.outer .inner` | Nested elements (with spaces) |

### Real Examples from Our Testing

**✅ Correct:**
```cmd
# Single class
--selector ".product-detail__content"

# ID selector  
--selector "article#post-2757"

# Multiple classes on same element
--selector ".product-detail__section.product-detail__section--gray.product-detail__section--tabs"

# Element with class
--selector "div.site-branding.branding-layout-standard"
```

**❌ Incorrect:**
```cmd
# Missing dot for class
--selector "product-detail__content"

# Spaces between classes on same element  
--selector ".product-detail__section .product-detail__section--gray .product-detail__section--tabs"

# Quotes around individual classes
--selector "'.content'"
```

## 🔧 File and Directory Setup

### Directory Structure
```
your-project/
├── my_urls.txt          # Your URLs file
├── output/              # Generated files go here
└── imports/             # Optional: organize your imports
```

### Creating Output Directories
```cmd
REM Option 1: Let the tool create directories
run.bat wordpress urls.txt --output "imports/blog_migration"

REM Option 2: Create directory first  
mkdir imports
run.bat wordpress urls.txt --output "imports/my_content"

REM Option 3: Use default output directory
run.bat wordpress urls.txt --output "my_import"
```

## 🎯 Real-World Examples

### Example 1: Blog Post Migration
**Goal**: Migrate 5 blog posts from an external WordPress site

1. **Create URLs file** (`blog_posts.txt`):
```
https://external-blog.com/how-to-do-seo/
https://external-blog.com/content-marketing-tips/
https://external-blog.com/social-media-strategy/
```

2. **Run migration**:
```cmd
run.bat wordpress blog_posts.txt --output "blog_migration"
```

3. **Result**: `blog_migration.xml` ready for WordPress import

### Example 2: Product Pages with Specific Content
**Goal**: Extract specific product information sections

1. **Create URLs file** (`products.txt`):
```
https://company.com/products/widget-a/
https://company.com/products/widget-b/
```

2. **Run with specific selector**:
```cmd
run.bat wordpress products.txt --selector ".product-detail__content" --output "product_imports"
```

### Example 3: Single Article Extraction  
**Goal**: Get one specific article section

**Direct approach**:
```cmd
run.bat scrape "https://site.com/article/" --selector "article#post-2757" --output "single_article"
```

**WordPress XML approach**:
```cmd
REM Create single URL file
echo https://site.com/article/ > single_url.txt

REM Extract as WordPress XML
run.bat wordpress single_url.txt --selector "article#post-2757" --output "article_import"
```

## 🆘 Troubleshooting Common Issues

### Issue 1: "Invalid URL format" Error
**Problem**: URLs have quotes around them in your text file
```
"https://example.com/"  ❌ Wrong
```

**Solution**: Remove quotes from URLs
```
https://example.com/     ✅ Correct
```

### Issue 2: "No element found for selector"
**Problem**: CSS selector doesn't match anything on the page

**Solutions**:
1. **Use auto-detection** (remove `--selector` parameter):
```cmd
run.bat wordpress urls.txt --output "import_name"
```

2. **Try broader selectors**:
```cmd
REM Instead of specific classes, try:
--selector ".content"
--selector "main"
--selector "article"
```

3. **Check your selector syntax**:
```bash
# For <div class="content main">
--selector ".content.main"        ✅ Correct
--selector ".content .main"       ❌ Wrong (looks for nested)
--selector "content main"         ❌ Wrong (missing dots)
```

### Issue 3: Empty or Minimal Content
**Problem**: You're getting very little content

**Solutions**:
1. **Try a broader selector**:
```cmd
REM Instead of specific element, try parent container
--selector ".main-content"
--selector ".post-body"
--selector "article"
```

2. **Use auto-detection**:
```cmd
run.bat wordpress urls.txt --output "import_name"
```

### Issue 4: Image Processing Problems (v1.1+)
**Problem**: Images not downloading or processing correctly

**Common Solutions**:

**Images Too Large:**
```
>>> Image skipped: image.jpg (15MB exceeds 10MB limit)
```
Solution: Images over 10MB are automatically skipped for WordPress compatibility

**Image Format Issues:**
```
>>> Image skipped: image.bmp (unsupported format)
```
Solution: Only JPG, PNG, WebP, GIF, SVG, ICO formats supported

**Download Failures:**
```cmd
REM Check verbose output for details
run.bat wordpress urls.txt --verbose --output "import_name"
```

**Image Directory Issues:**
```cmd
REM Ensure write permissions for image directory
REM Images saved to: wordpress_images/[domain]/
```

### Issue 5: WordPress Import Problems
**Problem**: WordPress import fails or images missing

**Solutions**:

**Manual Image Upload:**
1. Find images in `wordpress_images/[domain]/` folder
2. Upload to WordPress Media Library manually
3. Update image URLs in imported posts

**Import File Size:**
```cmd
REM For large imports, WordPress may have file size limits
REM Split into smaller batches if needed
```

## 🖼️ Image Processing Features (v1.1+)

### Automatic Image Handling
The v1.1 architecture includes comprehensive image processing with multiple modes:

**Available Image Modes:**
- `absolute_urls` (default): Converts relative image URLs to absolute
- `download_local`: Downloads images to organized local directory
- `download_and_rehost`: Downloads images for WordPress media library rehosting
- `base64`: Embeds small images as base64 data

**WordPress Image Processing:**
```cmd
REM Images automatically downloaded for rehosting
run.bat wordpress urls.txt --output "import_name"

REM Custom image directory
run.bat wordpress urls.txt --output "import_name" 
```

**Image Organization:**
- Images stored by domain: `wordpress_images/example.com/image1.jpg`
- Alt text preserved from source pages
- Size limits and format filtering (JPG, PNG, WebP, GIF, SVG)
- Statistics tracking for processed images

**WordPress-Specific Image Settings:**
- **Max size**: 10MB limit for WordPress compatibility
- **Optimization**: Images optimized for web delivery (quality: 80%)
- **Media library ready**: Downloaded images ready for WordPress upload
- **Format support**: All common web formats including WebP and SVG

### Image Processing Output
```
>>> Processing images: 5 found, 4 downloaded, 1 skipped (too large)
>>> Images saved to: wordpress_images/example-site.com/
>>> Image statistics: Total: 5, Success: 4, Skipped: 1, Failed: 0
```

## ⚙️ Advanced Configuration

### WordPress-Specific Settings
The tool uses `config/wordpress.yaml` for WordPress migrations, which includes:
- **Lower rate limits**: More respectful of external sites
- **Longer timeouts**: Handles slow-loading pages
- **Content filtering**: Removes sidebars, comments, navigation
- **Draft import**: All content imported as drafts for review
- **Image processing**: Automatic download and optimization for WordPress

### Custom Configuration
```cmd
run.bat wordpress urls.txt --config "my_config.yaml" --output "import_name"
```

### Verbose Logging
```cmd
run.bat wordpress urls.txt --verbose --output "import_name"
```

## 📊 Understanding the Output

### Success Messages
```
>>> Found 3 URLs to migrate
>>> Scraping 1/3: https://example.com/post1/
>>> 1/3 - Success (2547 chars)
>>> Scraping 2/3: https://example.com/post2/  
>>> 2/3 - Success (1834 chars)
>>> Scraping 3/3: https://example.com/post3/
>>> 3/3 - Success (3021 chars)
>>> Exporting 3 posts to WordPress XML
>>> WordPress XML exported: my_import.xml
>>> Ready for import via WordPress Admin > Tools > Import > WordPress
```

### What the Numbers Mean
- **(2547 chars)**: Amount of content extracted
- **Success rate**: Percentage of URLs successfully processed
- **Duration**: Time taken per URL (includes ethical delays)

## 🔒 Ethical Usage

### Built-in Protections
- **Robots.txt compliance**: Automatically checks and respects robots.txt
- **Rate limiting**: Waits between requests to avoid overwhelming servers  
- **User-agent identification**: Clearly identifies itself in requests
- **Respectful delays**: Built-in delays between requests

### Best Practices
1. **Only scrape content you have permission to use**
2. **Respect rate limits** (tool enforces 15 requests/minute for WordPress mode)
3. **Check robots.txt manually** if unsure about permissions
4. **Start small** - test with 1-2 URLs before bulk processing

## 💡 Pro Tips

### Tip 1: Test First
Always test with a single URL before bulk processing:
```cmd
echo https://test-site.com/article/ > test.txt
run.bat wordpress test.txt --output "test_import"
```

### Tip 2: Use Meaningful Output Names
```cmd
REM Good names help you organize
run.bat wordpress blog_urls.txt --output "blog_migration_2025"
run.bat wordpress product_urls.txt --output "products_january"
```

### Tip 3: Check Content Before Import
Look at the generated XML file to verify content quality before importing to WordPress.

### Tip 4: Import as Drafts
The tool automatically imports content as drafts, so you can:
1. Review content quality
2. Make necessary edits  
3. Publish when ready

## 🎯 Quick Reference Card

```cmd
REM Basic WordPress migration
run.bat wordpress urls.txt --output "import_name"

REM With specific content selector  
run.bat wordpress urls.txt --selector ".content" --output "import_name"

REM Single article (alternative method)
run.bat scrape "https://site.com/article/" --selector "article" --output "article"

REM Verbose output for debugging
run.bat wordpress urls.txt --verbose --output "import_name"

REM Custom configuration
run.bat wordpress urls.txt --config "config/wordpress.yaml" --output "import_name"
```

## 🆘 Getting Help

### Built-in Help
```cmd
run.bat --help                    REM Main help
run.bat wordpress --help          REM WordPress command help
run.bat scrape --help            REM Single URL scraping help
```

### Test Functionality
```cmd
run.bat test                      REM Quick functionality test
```

### Common File Locations
- **Generated XML files**: Current directory or `output/` folder
- **Logs**: `logs/wordpress_migration.log`
- **Configuration**: `config/wordpress.yaml`

---

**Remember**: This tool is designed for ethical content migration. Always ensure you have permission to scrape and reuse content from external websites.

**Status**: Production ready for WordPress migrations up to 50 URLs at a time.