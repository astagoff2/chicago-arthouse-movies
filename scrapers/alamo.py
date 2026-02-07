"""Scraper for Alamo Drafthouse Wrigleyville."""
from .utils import make_request, logger
import json
from datetime import datetime
from collections import defaultdict


THEATER_INFO = {
    'name': 'Alamo Drafthouse',
    'url': 'https://drafthouse.com/chicago/theater/wrigleyville',
    'address': '3519 N Clark St'
}

# Wrigleyville cinema ID
WRIGLEYVILLE_CINEMA_ID = '1801'


def scrape_alamo():
    """Scrape Alamo Drafthouse Wrigleyville schedule via their API."""
    movies = []

    api_url = 'https://drafthouse.com/s/mother/v2/schedule/market/chicago'

    resp = make_request(api_url)
    if not resp:
        logger.error("Failed to fetch Alamo Drafthouse API")
        return movies

    try:
        data = resp.json().get('data', {})
    except json.JSONDecodeError:
        logger.error("Failed to parse Alamo Drafthouse JSON")
        return movies

    # Build presentation lookup (slug -> title)
    presentations = data.get('presentations', [])
    pres_lookup = {}
    for p in presentations:
        slug = p.get('slug')
        show = p.get('show', {})
        if slug and show:
            pres_lookup[slug] = {
                'title': show.get('title', ''),
                'year': show.get('year'),
                'slug': show.get('slug', slug)
            }

    # Get sessions (actual showtimes)
    sessions = data.get('sessions', [])

    # Group sessions by movie and date
    movie_sessions = defaultdict(lambda: defaultdict(list))

    for session in sessions:
        # Filter to Wrigleyville only
        cinema_id = str(session.get('cinemaId', ''))
        if cinema_id != WRIGLEYVILLE_CINEMA_ID:
            continue

        pslug = session.get('presentationSlug')
        if pslug not in pres_lookup:
            continue

        # Parse date and time
        show_time_str = session.get('showTimeClt', '')
        if not show_time_str:
            continue

        try:
            dt = datetime.fromisoformat(show_time_str.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d')
            time_str = dt.strftime('%-I:%M %p')
        except (ValueError, TypeError):
            continue

        movie_info = pres_lookup[pslug]
        title = movie_info['title']

        # Skip non-movie items
        skip = ['menu', 'gift', 'membership', 'party', 'rental', 'private']
        if any(s in title.lower() for s in skip):
            continue

        movie_sessions[title][date_str].append({
            'time': time_str,
            'year': movie_info.get('year'),
            'slug': movie_info.get('slug')
        })

    # Convert to movie entries
    for title, dates in movie_sessions.items():
        for date_str, times_list in dates.items():
            times = sorted(set(t['time'] for t in times_list))
            year = times_list[0].get('year')
            slug = times_list[0].get('slug', '')

            ticket_url = f"https://drafthouse.com/chicago/show/{slug}" if slug else THEATER_INFO['url']

            movies.append({
                'title': title,
                'theater': THEATER_INFO['name'],
                'theater_url': THEATER_INFO['url'],
                'address': THEATER_INFO['address'],
                'date': date_str,
                'times': times if times else ['See website'],
                'format': None,
                'director': None,
                'year': year,
                'ticket_url': ticket_url
            })

    logger.info(f"Alamo Drafthouse: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_alamo()
    for m in sorted(results, key=lambda x: (x['date'], x['title'])):
        print(f"{m['date']} - {m['title']} @ {m['times']}")
