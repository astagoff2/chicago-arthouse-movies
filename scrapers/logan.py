"""Scraper for Logan Theatre."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_time, clean_text, logger
import re
from datetime import datetime


THEATER_INFO = {
    'name': 'Logan Theatre',
    'url': 'https://www.thelogantheatre.com',
    'address': '2646 N Milwaukee Ave'
}


def scrape_logan():
    """Scrape Logan Theatre schedule."""
    movies = []
    base_url = 'https://www.thelogantheatre.com'

    resp = make_request(f'{base_url}/?p=showtimes')
    if not resp:
        resp = make_request(base_url)

    if not resp:
        logger.error("Failed to fetch Logan Theatre")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    today = datetime.now().strftime('%Y-%m-%d')

    # Find moviepad elements
    movie_pads = soup.find_all(class_='moviepad')

    for pad in movie_pads:
        # Title is in the img tag's title attribute
        img = pad.find('img')
        if not img:
            continue

        title = img.get('title', '').strip()
        if not title:
            # Try alt attribute
            title = img.get('alt', '').strip()
        if not title:
            continue

        # Find showtimes
        showtime_links = pad.find_all('a', href=True)
        times = []
        for link in showtime_links:
            link_text = link.get_text().strip()
            # Match time patterns like "1:00p" or "7:30p"
            if re.match(r'\d{1,2}:\d{2}[ap]', link_text, re.I):
                time_normalized = parse_time(link_text + 'm')
                if time_normalized and time_normalized not in times:
                    times.append(time_normalized)

        if not times:
            continue

        # Get ticket URL
        ticket_link = pad.find('a', href=re.compile(r'formovietickets|ticket'))
        ticket_url = ticket_link['href'] if ticket_link else f'{base_url}/showtimes'

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': today,
            'times': times,
            'format': None,
            'director': None,
            'year': None,
            'ticket_url': ticket_url
        })

    logger.info(f"Logan Theatre: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_logan()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
