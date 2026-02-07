"""Scraper for Gene Siskel Film Center."""
from bs4 import BeautifulSoup
from .utils import make_request, parse_date, parse_time, clean_text, logger
import re
from datetime import datetime, timedelta


THEATER_INFO = {
    'name': 'Gene Siskel Film Center',
    'url': 'https://www.siskelfilmcenter.org',
    'address': '164 N State St'
}


def scrape_siskel():
    """Scrape Gene Siskel Film Center schedule."""
    movies = []
    base_url = 'https://www.siskelfilmcenter.org'

    # Try the calendar/showtimes page
    resp = make_request(f'{base_url}/calendar')
    if not resp:
        resp = make_request(base_url)

    if not resp:
        logger.error("Failed to fetch Gene Siskel Film Center")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    current_year = datetime.now().year

    # Siskel uses Agile Ticketing externally, but may have listings on main site
    # Look for film/event listings
    film_sections = soup.find_all(['div', 'article', 'section'],
                                   class_=re.compile(r'film|movie|show|event|program', re.I))

    if not film_sections:
        # Try finding any links to films
        film_sections = soup.find_all('a', href=re.compile(r'/films|/shows|/events'))

    seen = set()

    for section in film_sections:
        title_elem = section.find(['h2', 'h3', 'h4', 'a'])
        if not title_elem:
            continue

        title = clean_text(title_elem.get_text())
        if not title or len(title) < 2:
            continue

        # Skip navigation items
        skip = ['showtimes', 'festivals', 'events', 'support', 'visit', 'about', 'calendar']
        if title.lower() in skip:
            continue

        if title in seen:
            continue
        seen.add(title)

        text = clean_text(section.get_text())

        # Find dates
        date_match = re.search(
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}',
            text, re.I
        )
        date_str = parse_date(date_match.group(0), current_year) if date_match else None

        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')

        # Find times
        time_matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:pm|am)?)', text, re.I)
        times = [parse_time(t) for t in time_matches if t]

        # Find director
        dir_match = re.search(r'(?:dir(?:ector)?\.?:?\s*)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        director = dir_match.group(1) if dir_match else None

        # Find year
        year_match = re.search(r'\((\d{4})\)', text)
        year = int(year_match.group(1)) if year_match else None

        # Find format
        format_match = re.search(r'(35mm|70mm|16mm|DCP)', text, re.I)
        film_format = format_match.group(1) if format_match else None

        # Get link
        link = section.find('a', href=True)
        film_url = link['href'] if link else f"{base_url}/calendar"
        if film_url and not film_url.startswith('http'):
            film_url = base_url + film_url

        movies.append({
            'title': title,
            'theater': THEATER_INFO['name'],
            'theater_url': THEATER_INFO['url'],
            'address': THEATER_INFO['address'],
            'date': date_str,
            'times': times if times else ['See website'],
            'format': film_format,
            'director': director,
            'year': year,
            'ticket_url': film_url
        })

    logger.info(f"Gene Siskel: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_siskel()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
