"""Scraper for Logan Theatre."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_time, clean_text, logger
import re
from datetime import datetime


THEATER_INFO = {
    'name': 'Logan Theatre',
    'url': 'https://thelogantheatre.com',
    'address': '2646 N Milwaukee Ave'
}


def scrape_logan():
    """Scrape Logan Theatre schedule."""
    movies = []
    base_url = 'https://thelogantheatre.com'

    resp = make_request(base_url)
    if not resp:
        logger.error("Failed to fetch Logan Theatre")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    today = datetime.now().strftime('%Y-%m-%d')

    # Logan shows movies with titles and showtimes
    # Look for movie title links - they typically link to movie detail pages

    # Find all anchor tags that could be movie titles
    # Movie titles are usually in links that aren't navigation
    all_links = soup.find_all('a', href=True)

    seen = set()

    for link in all_links:
        href = link.get('href', '')
        title = clean_text(link.get_text())

        # Skip navigation, empty, or short titles
        if not title or len(title) < 3:
            continue

        # Skip obvious navigation
        nav_words = ['menu', 'home', 'movies', 'events', 'membership', 'food', 'drink',
                     'info', 'contact', 'about', 'facebook', 'twitter', 'instagram',
                     'privacy', 'terms', 'buy tickets', 'trailer', 'more info']
        if title.lower() in nav_words or any(n in title.lower() for n in ['@', 'http', '.com']):
            continue

        # Look for movie-like patterns (avoid times, prices)
        if re.match(r'^\d{1,2}:\d{2}', title) or re.match(r'^\$', title):
            continue

        # Get parent to find associated times
        parent = link.find_parent(['div', 'li', 'article', 'section'])
        if not parent:
            continue

        parent_text = clean_text(parent.get_text())

        # Find showtimes in parent - pattern like "1:00p" or "7:00 PM"
        time_pattern = r'(\d{1,2}:\d{2}\s*[ap]\.?m?\.?)'
        time_matches = re.findall(time_pattern, parent_text, re.I)

        if not time_matches:
            continue

        times = []
        for t in time_matches[:6]:  # Limit to 6 times
            normalized = parse_time(t)
            if normalized and normalized not in times:
                times.append(normalized)

        if not times:
            continue

        # Check if this looks like a real movie title (has reasonable length, not all caps nav)
        if title in seen:
            continue
        if len(title) > 100:  # Too long, probably grabbed extra text
            continue

        seen.add(title)

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': today,  # Logan shows today's schedule
            'times': times,
            'format': None,
            'director': None,
            'year': None,
            'ticket_url': base_url
        })

    logger.info(f"Logan Theatre: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_logan()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
