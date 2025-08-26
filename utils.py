from bs4 import BeautifulSoup
from urllib.parse import urljoin
from slugify import slugify

def extract_content(html, selector, base_url=""):
    soup = BeautifulSoup(html, "lxml")
    section = soup.select_one(selector)
    if not section:
        raise ValueError(f"No element found for selector: {selector}")
    
    images = []
    for img in section.find_all("img"):
        src = img.get("src")
        if src:
            abs_src = urljoin(base_url, src)
            images.append(abs_src)
            img["src"] = abs_src

    return str(section), images

def get_slug_from_title(title: str):
    return slugify(title.strip().lower())