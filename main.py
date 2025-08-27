import asyncio
import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from utils import setup_logging, load_config
from scraper import EthicalScraper
from exporter import ContentExporter
from exceptions import handle_exception, EWSException

app = typer.Typer(help="Ethical Web Scraper - A tool for responsible web scraping")
console = Console()

@app.command()
def scrape(
    url: str = typer.Argument(..., help="URL to scrape"),
    selector: str = typer.Option("body", "--selector", "-s", help="CSS selector for content extraction"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename (without extension)"),
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, csv, xml, all"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
    respect_robots: bool = typer.Option(True, "--robots/--no-robots", help="Respect robots.txt"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Scrape a specific section of a webpage and export it."""
    
    try:
        # Setup logging
        log_level = "DEBUG" if verbose else "INFO"
        logger = setup_logging({"logging": {"level": log_level}})
        
        # Load configuration
        config = load_config(config_file) if config_file else load_config()
        if not respect_robots:
            config['scraping']['respect_robots_txt'] = False
        if not headless:
            config['browser']['headless'] = False
            
        console.print(f"[blue]>>>[/blue] Starting scrape: [bold cyan]{url}[/bold cyan]")
        console.print(f"[blue]>>>[/blue] Selector: [yellow]{selector}[/yellow]")
        
        # Run scraping
        result = asyncio.run(_scrape_single(url, selector, config))
        
        if result:
            # Export results
            exporter = ContentExporter(config)
            
            if format.lower() == "all":
                formats = ["json", "csv", "xml"]
            else:
                formats = [format.lower()]
                
            for fmt in formats:
                try:
                    if fmt == "json":
                        filepath = exporter.export_json(result, output)
                    elif fmt == "csv":
                        filepath = exporter.export_csv([result], output)
                    elif fmt == "xml":
                        filepath = exporter.export_xml([result], output)
                    else:
                        console.print(f"[red]❌ Unknown format: {fmt}[/red]")
                        continue
                        
                    console.print(f"[green]>>> Exported {fmt.upper()}: {filepath}[/green]")
                except Exception as e:
                    console.print(f"[red]❌ Export failed ({fmt}): {e}[/red]")
                    
            # Display summary
            _display_summary(result)
            
        else:
            console.print("[red]>>> Scraping failed - no content returned[/red]")
            raise typer.Exit(1)
            
    except EWSException as e:
        handle_exception(e)
        console.print(f"[red]>>> {e.code}: {e}[/red]")
        if e.recovery_action:
            console.print(f"[yellow]>>> Recovery: {e.recovery_action}[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Unexpected error: {e}")
        console.print(f"[red]>>> Unexpected error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def batch(
    urls_file: str = typer.Argument(..., help="File containing URLs to scrape (one per line)"),
    selector: str = typer.Option("body", "--selector", "-s", help="CSS selector for content extraction"),
    output_dir: Optional[str] = typer.Option("output", "--output-dir", "-d", help="Output directory"),
    format: str = typer.Option("json", "--format", "-f", help="Export format: json, csv, xml"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to configuration file"),
    respect_robots: bool = typer.Option(True, "--robots/--no-robots", help="Respect robots.txt"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")
):
    """Batch scrape multiple URLs from a file."""
    
    try:
        # Setup logging
        log_level = "DEBUG" if verbose else "INFO"
        logger = setup_logging({"logging": {"level": log_level}})
        
        # Load URLs
        urls_path = Path(urls_file)
        if not urls_path.exists():
            console.print(f"[red]>>> URLs file not found: {urls_file}[/red]")
            raise typer.Exit(1)
            
        urls = []
        with urls_path.open() as f:
            for line in f:
                url = line.strip()
                if url and not url.startswith('#'):
                    urls.append(url)
                    
        if not urls:
            console.print("[red]>>> No URLs found in file[/red]")
            raise typer.Exit(1)
            
        console.print(f"[blue]>>>[/blue] Found {len(urls)} URLs to scrape")
        
        # Load configuration
        config = load_config(config_file) if config_file else load_config()
        if not respect_robots:
            config['scraping']['respect_robots_txt'] = False
            
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Run batch scraping
        results = asyncio.run(_scrape_batch(urls, selector, config))
        
        if results:
            # Export results
            exporter = ContentExporter(config)
            
            try:
                if format.lower() == "json":
                    filepath = exporter.export_json(results, str(output_path / "batch_results"))
                elif format.lower() == "csv":
                    filepath = exporter.export_csv(results, str(output_path / "batch_results"))
                elif format.lower() == "xml":
                    filepath = exporter.export_xml(results, str(output_path / "batch_results"))
                else:
                    console.print(f"[red]❌ Unknown format: {format}[/red]")
                    raise typer.Exit(1)
                    
                console.print(f"[green]>>> Batch export complete: {filepath}[/green]")
                console.print(f"[blue]>>>[/blue] Successfully scraped {len(results)} of {len(urls)} URLs")
                
            except Exception as e:
                console.print(f"[red]>>> Batch export failed: {e}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[red]>>> No content was successfully scraped[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Batch scraping error: {e}")
        console.print(f"[red]>>> Batch scraping failed: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def test():
    """Test the scraper with a simple example."""
    console.print("[blue]>>>[/blue] Running scraper test...")
    
    try:
        # Setup logging
        logger = setup_logging()
        
        # Use httpbin.org for testing
        test_url = "https://httpbin.org/html"
        console.print(f"[blue]>>>[/blue] Testing with URL: {test_url}")
        result = asyncio.run(_scrape_single(test_url, "body"))
        
        if result:
            console.print("[green]>>> Test successful![/green]")
            _display_summary(result)
        else:
            console.print("[red]>>> Test failed - no content returned[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]>>> Test failed: {e}[/red]")
        raise typer.Exit(1)

async def _scrape_single(url: str, selector: str, config: Optional[dict] = None):
    """Helper function to scrape a single URL."""
    if config is None:
        config = load_config()
    
    scraper = EthicalScraper(config)
    result = await scraper.scrape_url(url, selector)
    return result

async def _scrape_batch(urls: List[str], selector: str, config: dict):
    """Helper function to scrape multiple URLs."""
    scraper = EthicalScraper(config)
    results = []
    
    for i, url in enumerate(urls):
        console.print(f"[blue]>>>[/blue] Scraping {i+1}/{len(urls)}: {url}")
        
        try:
            result = await scraper.scrape_url(url, selector)
            if result:
                results.append(result)
                console.print(f"[green]>>> {i+1}/{len(urls)} - Success[/green]")
            else:
                console.print(f"[yellow]>>> {i+1}/{len(urls)} - No content[/yellow]")
        except Exception as e:
            console.print(f"[red]>>> {i+1}/{len(urls)} - Error: {str(e)[:50]}[/red]")
            
    return results

def _display_summary(result):
    """Display a summary of scraped content."""
    table = Table(title="Scrape Summary")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Title", result.title)
    table.add_row("URL", result.source_url)
    table.add_row("Content Length", f"{len(result.content_html)} chars")
    table.add_row("Images Found", str(len(result.images)))
    table.add_row("Scraped At", result.scraped_at)
    
    if result.metadata:
        table.add_row("Duration", f"{result.metadata.get('scrape_duration', 'N/A')}s")
    
    console.print(table)

if __name__ == "__main__":
    app()