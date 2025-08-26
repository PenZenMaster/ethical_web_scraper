import typer
from scraper import scrape_url

app = typer.Typer()

@app.command()
def scrape(url: str, selector: str = ".product-detail[product-detail]"):
    """Scrape a specific section of a webpage and export it to JSON."""
    typer.echo(f"Scraping URL: {url}")
    scrape_url(url, selector)

if __name__ == "__main__":
    app()