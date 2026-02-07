"""Scraper for Gene Siskel Film Center using Playwright."""
from .utils import clean_text, logger
import re
from datetime import datetime

THEATER_INFO = {
    'name': 'Gene Siskel Film Center',
    'url': 'https://www.siskelfilmcenter.org',
    'address': '164 N State St'
}


def scrape_siskel():
    """Scrape Gene Siskel Film Center schedule using Playwright."""
    movies = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed - skipping Siskel")
        return movies

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to the main page
            page.goto(THEATER_INFO['url'], timeout=30000)

            # Wait for content to load
            page.wait_for_timeout(3000)

            # Get the page content
            content = page.content()
            browser.close()

    except Exception as e:
        logger.error(f"Playwright error for Siskel: {e}")
        return movies

    # Parse the rendered HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'lxml')

    current_year = datetime.now().year
    today = datetime.now().strftime('%Y-%m-%d')

    seen = set()

    # Look for film titles in the rendered content
    # Siskel displays films with title (director, year) format
    page_text = soup.get_text()

    # Pattern: "Title (Director, Year)" or "Title (Year)"
    pattern = r'([A-Z][A-Za-z\s\'\:\,\-\.\&]+?)\s*\(([^)]*\d{4})\)'
    matches = re.findall(pattern, page_text)

    for title, info in matches:
        title = clean_text(title)

        # Skip navigation/generic items
        if not title or len(title) < 3 or len(title) > 80:
            continue

        skip = ['gene siskel', 'film center', 'school of', 'art institute',
                'chicago', 'illinois', 'member', 'ticket', 'state street',
                'box office', 'visit', 'support', 'about']
        if any(s in title.lower() for s in skip):
            continue

        if title in seen:
            continue
        seen.add(title)

        # Extract year from info
        year_match = re.search(r'(\d{4})', info)
        year = int(year_match.group(1)) if year_match else None

        # Extract director if present
        director = None
        if ',' in info:
            parts = info.split(',')
            if len(parts) >= 2:
                director = clean_text(parts[0])

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': today,
            'times': ['See website'],
            'format': None,
            'director': director,
            'year': year,
            'ticket_url': f"{THEATER_INFO['url']}/showtimes"
        })

    logger.info(f"Gene Siskel: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_siskel()
    for m in results:
        print(f"{m['date']} - {m['title']} ({m.get('year', '?')})")
