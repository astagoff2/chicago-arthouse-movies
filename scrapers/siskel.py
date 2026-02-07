"""Scraper for Gene Siskel Film Center using Playwright."""
from .utils import clean_text, logger
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

            # Go to the calendar page
            page.goto(f"{THEATER_INFO['url']}/playing-this-month", timeout=30000)

            # Wait for content to load
            page.wait_for_timeout(5000)

            # Get the page content
            content = page.content()
            browser.close()

    except Exception as e:
        logger.error(f"Playwright error for Siskel: {e}")
        return movies

    # Parse the rendered HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'lxml')

    today = datetime.now().strftime('%Y-%m-%d')
    seen = set()

    # Find the calendar view and extract film links
    calendar = soup.find(class_='view-monthly-calendar')
    if not calendar:
        logger.warning("Siskel: Could not find calendar view")
        return movies

    for a in calendar.find_all('a', href=True):
        href = a.get('href', '')
        title = a.get_text(strip=True)

        # Skip navigation links
        if not title or len(title) < 3:
            continue
        if 'next month' in title.lower() or 'previous' in title.lower():
            continue

        # Clean up title
        title = clean_text(title)

        # Skip duplicates
        if title in seen:
            continue
        seen.add(title)

        # Build ticket URL
        ticket_url = f"{THEATER_INFO['url']}{href}" if href.startswith('/') else href

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': today,
            'times': ['See website'],
            'format': None,
            'director': None,
            'year': None,
            'ticket_url': ticket_url
        })

    logger.info(f"Gene Siskel: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_siskel()
    for m in results:
        print(f"{m['title']} -> {m['ticket_url']}")
