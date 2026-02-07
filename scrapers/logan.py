"""Scraper for Logan Theatre."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, parse_time, clean_text, logger
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
    current_year = datetime.now().year

    # Logan has movie cards with posters and showtimes
    # Look for movie containers
    movie_containers = soup.find_all(['div', 'article'], class_=re.compile(r'movie|film|show', re.I))

    if not movie_containers:
        # Try finding by structure - look for items with images and showtimes
        movie_containers = soup.find_all('div', recursive=True)

    seen = set()

    for container in movie_containers:
        # Look for title
        title_elem = container.find(['h2', 'h3', 'h4'])
        if not title_elem:
            continue

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            continue

        # Skip if we've seen this
        if title in seen:
            continue

        text = clean_text(container.get_text())

        # Skip navigation elements
        if title.lower() in ['movies', 'events', 'membership', 'food', 'drink', 'info']:
            continue

        seen.add(title)

        # Find showtimes
        time_matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:pm|am)?)', text, re.I)
        times = [parse_time(t) for t in time_matches if t]

        # Find rating
        rating_match = re.search(r'\b(G|PG|PG-13|R|NC-17|NR)\b', text)

        # Find runtime
        runtime_match = re.search(r'(\d+)\s*(?:min|minutes)', text, re.I)

        # Look for dates in the container
        date_text = container.find(class_=re.compile(r'date', re.I))
        date_str = None
        if date_text:
            date_str = parse_date(clean_text(date_text.get_text()), current_year)

        if not date_str:
            # Default to today
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Get link to movie page
        link = container.find('a', href=True)
        movie_url = link['href'] if link else base_url
        if movie_url and not movie_url.startswith('http'):
            movie_url = base_url + movie_url

        if times:  # Only add if we found showtimes
            movies.append({
                'title': title,
                'theater': THEATER_INFO['name'],
                'theater_url': THEATER_INFO['url'],
                'address': THEATER_INFO['address'],
                'date': date_str,
                'times': times if times else ['See website'],
                'format': None,
                'director': None,
                'year': None,
                'ticket_url': movie_url
            })

    logger.info(f"Logan Theatre: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_logan()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
