"""Scraper for Gene Siskel Film Center."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, parse_time, clean_text, logger
import re
from datetime import datetime


THEATER_INFO = {
    'name': 'Gene Siskel Film Center',
    'url': 'https://www.siskelfilmcenter.org',
    'address': '164 N State St'
}


def scrape_siskel():
    """Scrape Gene Siskel Film Center schedule."""
    movies = []
    base_url = 'https://www.siskelfilmcenter.org'

    resp = make_request(base_url)
    if not resp:
        logger.error("Failed to fetch Gene Siskel Film Center")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    current_year = datetime.now().year
    today = datetime.now().strftime('%Y-%m-%d')

    # Siskel shows films in a carousel/grid format
    # Look for film titles which are typically in headings or strong links

    # Find film cards/entries - look for elements with film info
    # Films have titles like "A Poet (2025)" or just "A Poet"

    seen = set()

    # Try to find film entries by looking for title patterns
    # Search for text that looks like "Title (Year)" or linked titles
    all_text = soup.get_text()

    # Pattern for "Title (Director, Year)" or "Title (Year)"
    title_year_pattern = r'([A-Z][A-Za-z\s\':,\-\.]+?)\s*\((?:[^)]*,\s*)?(\d{4})\)'
    matches = re.findall(title_year_pattern, all_text)

    for title, year in matches:
        title = clean_text(title)

        # Skip navigation/generic items
        if not title or len(title) < 3 or len(title) > 80:
            continue
        skip = ['gene siskel', 'film center', 'school of', 'art institute',
                'chicago', 'illinois', 'member', 'ticket', 'today', 'this week']
        if any(s in title.lower() for s in skip):
            continue

        if title in seen:
            continue
        seen.add(title)

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': today,
            'times': ['See website'],
            'format': None,
            'director': None,
            'year': int(year),
            'ticket_url': f"{base_url}/showtimes"
        })

    # Also look for linked titles that might not have years
    title_links = soup.find_all('a', href=re.compile(r'/films/|/events/|/shows/'))
    for link in title_links:
        title = clean_text(link.get_text())
        if not title or len(title) < 3 or title in seen:
            continue
        skip = ['showtimes', 'calendar', 'events', 'films', 'more', 'view']
        if title.lower() in skip:
            continue
        seen.add(title)

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
            'ticket_url': base_url + link.get('href', '/showtimes')
        })

    logger.info(f"Gene Siskel: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_siskel()
    for m in results:
        print(f"{m['date']} - {m['title']} ({m.get('year', '?')})")
