"""Scraper for Alamo Drafthouse Wrigleyville."""
from .utils import make_request, clean_text, logger
import re
import json
from datetime import datetime


THEATER_INFO = {
    'name': 'Alamo Drafthouse',
    'url': 'https://drafthouse.com/chicago/theater/wrigleyville',
    'address': '3519 N Clark St'
}


def scrape_alamo():
    """Scrape Alamo Drafthouse Wrigleyville schedule.

    Note: Alamo uses JavaScript rendering, so this scraper attempts to
    find any embedded JSON data or API endpoints. If that fails, it
    returns a placeholder entry directing users to the website.
    """
    movies = []
    base_url = 'https://drafthouse.com'
    theater_url = f'{base_url}/chicago/theater/wrigleyville'

    # Try to fetch the page
    resp = make_request(theater_url)

    today = datetime.now().strftime('%Y-%m-%d')

    if resp:
        # Look for embedded JSON data (some sites include this for SEO)
        text = resp.text

        # Try to find JSON-LD or embedded data
        json_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                # Parse if it contains movie info
                if isinstance(data, dict) and 'event' in str(data).lower():
                    logger.info("Found JSON-LD data in Alamo page")
            except json.JSONDecodeError:
                pass

        # Look for any movie titles in the raw HTML
        title_pattern = r'"name"\s*:\s*"([^"]+)"'
        titles = re.findall(title_pattern, text)

        seen = set()
        for title in titles:
            if len(title) > 3 and len(title) < 80 and title not in seen:
                # Skip non-movie items
                skip = ['alamo', 'drafthouse', 'wrigleyville', 'chicago', 'menu',
                        'gift', 'membership', 'victory', 'season pass']
                if any(s in title.lower() for s in skip):
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
                    'ticket_url': theater_url
                })

    # If we couldn't scrape anything, the site likely needs JavaScript
    # Don't add a placeholder - just return empty and let other theaters show
    if not movies:
        logger.warning("Alamo Drafthouse requires JavaScript - no movies scraped")

    logger.info(f"Alamo Drafthouse: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_alamo()
    for m in results:
        print(f"{m['date']} - {m['title']}")
