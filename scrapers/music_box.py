"""Scraper for Music Box Theatre."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, clean_text, logger
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

    # Find all showtime blocks
    showtime_blocks = soup.find_all(class_='programming-showtimes')

    for block in showtime_blocks:
        # Get the full text which contains date and times
        text = block.get_text(strip=True)
        if not text:
            continue

        # Parse date - format like "Sat, Feb 7" or "Sun, Feb 8"
        # The date ends where the time begins (a digit followed by colon)
        date_match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2})(?=\d{1,2}:|\s|$)', text, re.I)
        if not date_match:
            continue

        date_str = date_match.group(1)
        date = parse_date(date_str, current_year)
        if not date:
            continue

        # Parse times - they come after the date, separated by /
        # Extract everything after the date
        time_portion = text[date_match.end():]
        # Find all times like "11:30am" or "7:00pm"
        times = re.findall(r'(\d{1,2}:\d{2}\s*(?:am|pm))', time_portion, re.I)
        if not times:
            continue

        # Find the associated film title
        parent = block.find_parent(['div', 'article', 'li'])
        if not parent:
            continue

        title_link = parent.find('a', href=re.compile(r'/films-and-events/'))
        if not title_link:
            continue

        title = clean_text(title_link.get_text())
        if not title or len(title) < 3:
            continue

        # Get ticket URL
        ticket_url = title_link.get('href', '')
        if not ticket_url.startswith('http'):
            ticket_url = base_url + ticket_url

        # Find format (35mm, 70mm, DCP, etc.)
        parent_text = parent.get_text()
        format_match = re.search(r'\b(35mm|70mm|16mm|DCP|3D DCP)\b', parent_text, re.I)
        film_format = format_match.group(1) if format_match else None

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': date,
            'times': times,
            'format': film_format,
            'director': None,
            'year': None,
            'ticket_url': ticket_url
        })

    logger.info(f"Music Box: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_music_box()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
