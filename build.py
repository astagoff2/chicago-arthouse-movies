#!/usr/bin/env python3
"""Build script for Chicago Art House Cinema website."""
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

CHICAGO_TZ = ZoneInfo('America/Chicago')

from jinja2 import Environment, FileSystemLoader

# Add scrapers to path
sys.path.insert(0, str(Path(__file__).parent))

from scrapers import (
    scrape_doc_films,
    scrape_music_box,
    scrape_logan,
    scrape_facets,
    scrape_siskel,
    scrape_alamo
)
from scrapers.letterboxd import enrich_movies_with_letterboxd


def format_day(date_str):
    """Format date as 'Friday, February 7'."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%A, %B %-d')
    except (ValueError, TypeError):
        return date_str


def filter_to_week(movies):
    """Filter movies to only include this week (next 7 days)."""
    today = datetime.now(CHICAGO_TZ).date()
    week_end = today + timedelta(days=7)

    filtered = []
    for movie in movies:
        try:
            movie_date = datetime.strptime(movie['date'], '%Y-%m-%d').date()
            if today <= movie_date <= week_end:
                filtered.append(movie)
        except (ValueError, TypeError):
            continue
    return filtered


def run_scrapers():
    """Run all scrapers and collect movies."""
    all_movies = []

    scrapers = [
        ('Gene Siskel', scrape_siskel),
        ('Doc Films', scrape_doc_films),
        ('Music Box', scrape_music_box),
        ('Logan Theatre', scrape_logan),
        ('Facets', scrape_facets),
        ('Alamo Drafthouse', scrape_alamo),
    ]

    for name, scraper in scrapers:
        try:
            print(f"Scraping {name}...")
            movies = scraper()
            all_movies.extend(movies)
            print(f"  Found {len(movies)} screenings")
        except Exception as e:
            print(f"  Error scraping {name}: {e}")

    # Filter to current week only
    all_movies = filter_to_week(all_movies)
    print(f"\nFiltered to {len(all_movies)} screenings this week")

    return all_movies


def save_data(movies, output_path):
    """Save movies to JSON file."""
    data = {
        'last_updated': datetime.now().isoformat(),
        'week_of': datetime.now().strftime('%Y-%m-%d'),
        'movies': movies
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(movies)} screenings to {output_path}")


def time_sort_key(movie):
    """Convert first showtime to sortable value."""
    times = movie.get('times', [])
    if not times or times[0] == 'See website':
        return (2, 0)  # Put "See website" at end

    time_str = times[0].lower().strip()
    try:
        # Parse time like "7:00 pm" or "11:30am"
        import re
        match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            is_pm = match.group(3) == 'pm'

            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0

            return (0, hour * 60 + minute)
    except:
        pass
    return (1, 0)  # Unknown times in middle


def group_by_date(movies):
    """Group movies by date, sorted chronologically, with times sorted within each day."""
    by_date = defaultdict(list)
    for movie in movies:
        by_date[movie['date']].append(movie)

    # Sort dates and sort movies within each date by showtime
    sorted_dates = sorted(by_date.keys())
    return {date: sorted(by_date[date], key=time_sort_key) for date in sorted_dates}


def generate_html(movies, template_dir, output_path):
    """Generate static HTML from template."""
    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['format_day'] = format_day

    template = env.get_template('index_template.html')

    movies_by_date = group_by_date(movies)

    # Get unique theaters
    theaters = sorted(set(m['theater'] for m in movies))

    # Get tonight's movies
    today = datetime.now(CHICAGO_TZ).strftime('%Y-%m-%d')
    tonight_movies = [m for m in movies if m['date'] == today]

    html = template.render(
        movies_by_date=movies_by_date,
        theaters=theaters,
        tonight_movies=tonight_movies,
        week_of=datetime.now().strftime('%B %-d, %Y'),
        last_updated=datetime.now().strftime('%B %-d at %-I:%M %p')
    )

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Generated {output_path}")


def main():
    """Main build process."""
    base_dir = Path(__file__).parent
    data_dir = base_dir / 'data'
    site_dir = base_dir / 'site'
    template_dir = base_dir / 'templates'

    # Ensure directories exist
    data_dir.mkdir(exist_ok=True)
    site_dir.mkdir(exist_ok=True)

    print("=" * 50)
    print("Chicago Art House Cinema - Build")
    print("=" * 50)
    print()

    # Run scrapers
    movies = run_scrapers()

    if not movies:
        print("\nNo movies found. Using sample data for testing.")
        movies = [
            {
                'title': 'Sample Film',
                'theater': 'Music Box Theatre',
                'theater_url': 'https://musicboxtheatre.com',
                'address': '3733 N Southport Ave',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'times': ['7:00 PM'],
                'format': '35mm',
                'director': 'Test Director',
                'year': 2024,
                'ticket_url': 'https://musicboxtheatre.com'
            }
        ]

    # Enrich with Letterboxd data
    print("\nFetching Letterboxd data...")
    movies = enrich_movies_with_letterboxd(movies)

    # Save data
    save_data(movies, data_dir / 'movies.json')

    # Generate HTML
    generate_html(movies, template_dir, site_dir / 'index.html')

    print()
    print("Build complete!")


if __name__ == '__main__':
    main()
