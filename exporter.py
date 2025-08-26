import json
from datetime import datetime
from pathlib import Path

def save_to_json(slug, url, html, images, output_dir="output"):
    Path(output_dir).mkdir(exist_ok=True)
    data = {
        "title": slug.replace("-", " ").title(),
        "slug": slug,
        "source_url": url,
        "content_html": html,
        "images": images,
        "scraped_at": datetime.utcnow().isoformat() + "Z"
    }
    path = Path(output_dir) / f"{slug}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Exported to {path}")