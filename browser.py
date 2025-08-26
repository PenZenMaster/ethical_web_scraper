from playwright.sync_api import sync_playwright

def load_rendered_html(url: str, timeout: int = 15000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=timeout)
        page.wait_for_load_state("networkidle")
        content = page.content()
        title = page.title()
        browser.close()
    return content, title