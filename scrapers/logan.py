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

    # Use the showtimes page
    resp = make_request(f'{base_url}/showtimes')
    if not resp:
        resp = make_request(base_url)

    if not resp:
        logger.error("Failed to fetch Logan Theatre")
        return movies

    soup = BeautifulSoup(resp.text, 'lxml')
    today = datetime.now().strftime('%Y-%m-%d')

    # Extract full page text and look for movie patterns
    # Logan format: "Movie Title - Rating" followed by times
    page_text = soup.get_text()

    # Find movie title elements - they're typically in specific divs/spans
    # Look for patterns like links with movie info
    movie_sections = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'movie|film|show', re.I))

    seen = set()

    # Also try parsing from the text directly
    # Pattern: movie titles followed by ratings and times
    lines = page_text.split('\n')
    current_title = None
    current_times = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # Check if this looks like a movie title (not a time, not navigation)
        # Movie titles are typically Title Case and reasonable length
        if (len(line) > 3 and len(line) < 60 and
            not re.match(r'^\d', line) and
            not line.lower() in ['movies', 'events', 'menu', 'home', 'contact', 'about']):

            # Check if next lines have times
            times_found = []
            for j in range(1, 4):
                if i + j < len(lines):
                    next_line = lines[i + j].strip()
                    time_matches = re.findall(r'(\d{1,2}:\d{2}\s*[ap])', next_line, re.I)
                    times_found.extend(time_matches)

            if times_found and line not in seen:
                # Skip navigation items
                skip = ['movie trivia', 'membership', 'gift card', 'coming soon',
                        'ticket pricing', 'now showing', 'food', 'drink', 'menu']
                if any(s in line.lower() for s in skip):
                    continue

                seen.add(line)
                times = [parse_time(t + 'm') for t in times_found[:6]]

                movies.append({
                    'title': line,
                    'theater': THEATER_INFO['name'],
                    'theater_url': THEATER_INFO['url'],
                    'address': THEATER_INFO['address'],
                    'date': today,
                    'times': times if times else ['See website'],
                    'format': None,
                    'director': None,
                    'year': None,
                    'ticket_url': f'{base_url}/showtimes'
                })

    logger.info(f"Logan Theatre: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_logan()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
