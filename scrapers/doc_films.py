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

    # Find film entries - look for links to calendar
    calendar_links = soup.find_all('a', href=re.compile(r'/calendar'))

    seen = set()

    for link in calendar_links:
        # Get the containing element
        parent = link.find_parent(['div', 'article', 'li', 'section'])
        if not parent:
            continue

        text = clean_text(parent.get_text())

        # Look for film title pattern: "Title (Year)"
        title_match = re.search(r'([A-Z][^(]+)\s*\((\d{4})\)', text)
        if not title_match:
            # Try simpler title extraction
            title_elem = parent.find(['h2', 'h3', 'h4', 'strong'])
            if title_elem:
                title = clean_text(title_elem.get_text())
                # Remove year if present
                title = re.sub(r'\s*\(\d{4}\)\s*$', '', title)
            else:
                continue
            year = None
        else:
            title = clean_text(title_match.group(1))
            year = int(title_match.group(2))

        if not title or len(title) < 2:
            continue

        # Create unique key
        key = f"{title}|{text[:50]}"
        if key in seen:
            continue
        seen.add(key)

        # Find date pattern: "Monday, February 3" or "Feb 3"
        date_match = re.search(
            r'(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+(\w+\s+\d{1,2})',
            text, re.I
        )
        date_str = None
        if date_match:
            date_str = parse_date(date_match.group(1), current_year)

        if not date_str:
            # Try simpler date pattern
            simple_date = re.search(r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2})', text, re.I)
            if simple_date:
                date_str = parse_date(simple_date.group(1), current_year)

        if not date_str:
            continue  # Skip if no date found

        # Find time pattern: "@ 7:00 PM" or "7:00 PM"
        time_match = re.search(r'@?\s*(\d{1,2}:\d{2}\s*(?:pm|am|PM|AM))', text)
        times = []
        if time_match:
            times.append(parse_time(time_match.group(1)))

        # Find format (35mm, 16mm, DCP, Digital)
        format_match = re.search(r'\b(35mm|16mm|DCP|[Dd]igital|70mm)\b', text)
        film_format = format_match.group(1) if format_match else None

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': date_str,
            'times': times if times else ['See website'],
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
