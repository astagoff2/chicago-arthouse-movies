"""Scraper for Music Box Theatre."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, parse_time, clean_text, logger
import re
from datetime import datetime


THEATER_INFO = {
    'name': 'Music Box Theatre',
    'url': 'https://musicboxtheatre.com',
    'address': '3733 N Southport Ave'
}


def scrape_music_box():
    """Scrape Music Box Theatre schedule."""
    movies = []
    base_url = 'https://musicboxtheatre.com'

    resp = make_request(f'{base_url}/calendar')
    if not resp:
        logger.error("Failed to fetch Music Box Theatre")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    current_year = datetime.now().year

    # Find all film title links (they link to /films-and-events/)
    film_links = soup.find_all('a', href=re.compile(r'/films-and-events/'))

    seen_films = {}  # title -> movie data

    for link in film_links:
        title = clean_text(link.get_text())

        # Skip short or generic titles
        if not title or len(title) < 3:
            continue

        # Skip navigation links
        skip_words = ['films', 'events', 'calendar', 'more', 'view all', 'series']
        if title.lower() in skip_words:
            continue

        # Get the parent container to find associated times
        parent = link.find_parent(['div', 'article', 'section', 'li'])
        if not parent:
            parent = link.parent

        # Get full text for parsing
        text = clean_text(parent.get_text()) if parent else title

        # Find format (35mm, 70mm, DCP, etc.)
        format_match = re.search(r'\b(35mm|70mm|16mm|DCP|3D DCP)\b', text, re.I)
        film_format = format_match.group(1) if format_match else None

        # Find dates - look for "Mon, Feb 7" or "Feb 7" patterns
        date_pattern = r'(?:(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}'
        date_matches = re.findall(date_pattern, text, re.I)

        # Find times
        time_matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:pm|am|PM|AM))', text)
        times = list(set([parse_time(t) for t in time_matches if t]))

        # Get ticket URL
        ticket_link = parent.find('a', href=re.compile(r'/order/')) if parent else None
        if ticket_link:
            ticket_url = ticket_link.get('href', '')
            if not ticket_url.startswith('http'):
                ticket_url = base_url + ticket_url
        else:
            ticket_url = base_url + link.get('href', '/calendar')

        # Process each date found
        dates_found = []
        for dm in date_matches[:7]:  # Limit to a week
            d = parse_date(dm, current_year)
            if d:
                dates_found.append(d)

        if not dates_found:
            continue  # Skip if no valid dates

        # Add entries
        for date in dates_found:
            key = f"{title}|{date}"
            if key not in seen_films:
                seen_films[key] = {
                    'title': title,
                    'theater': THEATER_INFO['name'],
                    'theater_url': THEATER_INFO['url'],
                    'address': THEATER_INFO['address'],
                    'date': date,
                    'times': times if times else ['See website'],
                    'format': film_format,
                    'director': None,
                    'year': None,
                    'ticket_url': ticket_url
                }

    movies = list(seen_films.values())
    logger.info(f"Music Box: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_music_box()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
