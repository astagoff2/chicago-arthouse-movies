#!/usr/bin/env python3
"""Build script for Chicago Art House Cinema website."""
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

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


def format_day(date_str):
    """Format date as 'Friday, February 7'."""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%A, %B %-d')
    except (ValueError, TypeError):
        return date_str


def filter_to_week(movies):
    """Filter movies to only include this week (next 7 days)."""
    today = datetime.now().date()
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


def group_by_date(movies):
    """Group movies by date, sorted chronologically."""
    by_date = defaultdict(list)
    for movie in movies:
        by_date[movie['date']].append(movie)

    # Sort dates and return as ordered dict
    sorted_dates = sorted(by_date.keys())
    return {date: by_date[date] for date in sorted_dates}


def generate_html(movies, template_dir, output_path):
    """Generate static HTML from template."""
    env = Environment(loader=FileSystemLoader(template_dir))
    env.filters['format_day'] = format_day

    template = env.get_template('index_template.html')

    movies_by_date = group_by_date(movies)

    html = template.render(
        movies_by_date=movies_by_date,
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

    # Save data
    save_data(movies, data_dir / 'movies.json')

    # Generate HTML
    generate_html(movies, template_dir, site_dir / 'index.html')

    print()
    print("Build complete!")


if __name__ == '__main__':
    main()
