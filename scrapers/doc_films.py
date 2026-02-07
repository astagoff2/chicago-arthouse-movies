"""Scraper for Doc Films (University of Chicago)."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, parse_time, clean_text, logger
import re
from datetime import datetime


THEATER_INFO = {
    'name': 'Doc Films',
    'url': 'https://docfilms.org',
    'address': 'Max Palevsky Cinema, Ida Noyes Hall, 1212 E 59th St'
}


def scrape_doc_films():
    """Scrape Doc Films weekly schedule."""
    movies = []
    url = 'https://docfilms.org'

    resp = make_request(url)
    if not resp:
        logger.error("Failed to fetch Doc Films")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    current_year = datetime.now().year

    # Get the full page text and parse it section by section
    # Doc Films has entries with pattern: "Title (Year)" followed by date/time

    # Find all links that go to calendar entries
    all_links = soup.find_all('a', href=re.compile(r'/calendar/'))

    # Group content by looking at text blocks
    page_text = soup.get_text()

    # Pattern: "Title (Year)" followed by day/date @ time and format
    # Example: "Night on Earth (1991)\nMonday, February 2 @ 7:00 PM\nDCP"
    pattern = r'([A-Z][^(]+?)\s*\((\d{4})\)\s*(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\w+\s+\d{1,2})\s*@\s*(\d{1,2}:\d{2}\s*[APap][Mm])\s*(35mm|16mm|DCP|[Dd]igital)?'

    matches = re.findall(pattern, page_text, re.MULTILINE)

    seen = set()
    for match in matches:
        title = clean_text(match[0])
        year = int(match[1])
        date_str = parse_date(match[2], current_year)
        time_str = parse_time(match[3])
        film_format = match[4] if len(match) > 4 and match[4] else None

        if not title or not date_str:
            continue

        key = f"{title}|{date_str}|{time_str}"
        if key in seen:
            continue
        seen.add(key)

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': date_str,
            'times': [time_str] if time_str else ['See website'],
            'format': film_format,
            'director': None,
            'year': year,
            'ticket_url': THEATER_INFO['url']
        })

    logger.info(f"Doc Films: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_doc_films()
    for m in results:
        print(f"{m['date']} - {m['title']} ({m.get('year', '?')}) @ {m['times']} [{m.get('format', '')}]")
