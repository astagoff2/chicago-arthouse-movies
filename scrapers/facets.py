"""Scraper for Facets Cinematheque."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, parse_time, clean_text, logger
import re
from datetime import datetime


THEATER_INFO = {
    'name': 'Facets',
    'url': 'https://www.facets.org',
    'address': '1517 W Fullerton Ave'
}


def scrape_facets():
    """Scrape Facets screening schedule."""
    movies = []
    base_url = 'https://www.facets.org'

    # Try calendar page first
    resp = make_request(f'{base_url}/calendar')
    if not resp:
        resp = make_request(base_url)

    if not resp:
        logger.error("Failed to fetch Facets")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    current_year = datetime.now().year

    # Facets uses program cards
    # Look for screening/event entries
    events = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'event|program|screening|film', re.I))

    if not events:
        # Try links to programs
        events = soup.find_all('a', href=re.compile(r'/program|/film|/event|/screening'))

    seen = set()

    for event in events:
        # Get title
        title_elem = event.find(['h2', 'h3', 'h4', 'strong'])
        if not title_elem:
            if event.name == 'a':
                title_elem = event
            else:
                continue

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            continue

        # Skip navigation and non-movie items
        skip_words = ['calendar', 'cinema', 'donate', 'about', 'contact', 'view all',
                      'film camps', 'film camp', 'critic\'s cut', 'critics cut',
                      'trivia', 'party', 'membership', 'gift', 'rental']
        title_lower = title.lower()
        if title_lower in skip_words or any(s in title_lower for s in skip_words):
            continue

        if title in seen:
            continue
        seen.add(title)

        text = clean_text(event.get_text())

        # Find dates
        # Pattern: "March 6" or "Feb 8 - March 1"
        date_match = re.search(
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}',
            text, re.I
        )
        date_str = None
        if date_match:
            date_str = parse_date(date_match.group(0), current_year)

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Find times
        time_matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:pm|am)?)', text, re.I)
        times = [parse_time(t) for t in time_matches if t]

        # Get link
        link = event.find('a', href=True) if event.name != 'a' else event
        event_url = link.get('href', base_url) if link else base_url
        if event_url and not event_url.startswith('http'):
            event_url = base_url + event_url

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
            'ticket_url': event_url
        })

    logger.info(f"Facets: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_facets()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
