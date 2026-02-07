"""Scraper for Alamo Drafthouse Wrigleyville."""
from .utils import make_request, clean_text, logger
import json
from datetime import datetime


THEATER_INFO = {
    'name': 'Alamo Drafthouse',
    'url': 'https://drafthouse.com/chicago/theater/wrigleyville',
    'address': '3519 N Clark St'
}


def scrape_alamo():
    """Scrape Alamo Drafthouse Wrigleyville schedule via their API."""
    movies = []

    # Alamo has a JSON API for their schedule
    api_url = 'https://drafthouse.com/s/mother/v2/schedule/market/chicago'

    resp = make_request(api_url)
    if not resp:
        logger.error("Failed to fetch Alamo Drafthouse API")
        return movies

    try:
        data = resp.json()
    except json.JSONDecodeError:
        logger.error("Failed to parse Alamo Drafthouse JSON")
        return movies

    today = datetime.now().strftime('%Y-%m-%d')
    seen = set()

    # The API returns data.presentations
    inner = data.get('data', data)
    presentations = inner.get('presentations', [])

    for item in presentations:
        # Get show info - title is nested in 'show' object
        show = item.get('show', {})
        if not isinstance(show, dict):
            continue

        title = show.get('title', '')
        if not title or title in seen:
            continue

        # Skip non-movie items
        skip = ['menu', 'gift', 'membership', 'party', 'rental', 'private']
        if any(s in title.lower() for s in skip):
            continue

        seen.add(title)

        # Get year and other info
        year = show.get('year')
        certification = show.get('certification')

        # Build ticket URL
        slug = item.get('slug') or show.get('slug', '')
        ticket_url = f"https://drafthouse.com/chicago/show/{slug}" if slug else THEATER_INFO['url']

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': today,
            'times': ['See website'],
            'format': None,
            'director': None,
            'year': year,
            'ticket_url': ticket_url
        })

    logger.info(f"Alamo Drafthouse: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_alamo()
    for m in results:
        print(f"{m['date']} - {m['title']} ({m.get('year', '?')})")
