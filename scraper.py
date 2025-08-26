from browser import load_rendered_html
from exporter import save_to_json
from utils import extract_content, get_slug_from_title

def scrape_url(url: str, selector: str):
    html, page_title = load_rendered_html(url)
    content, images = extract_content(html, selector, base_url=url)
    slug = get_slug_from_title(page_title or url)
    save_to_json(slug, url, content, images)