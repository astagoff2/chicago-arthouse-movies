"""Scraper for Gene Siskel Film Center using Playwright."""
from .utils import clean_text, logger
from datetime import datetime
import re

THEATER_INFO = {
    'name': 'Gene Siskel Film Center',
    'url': 'https://www.siskelfilmcenter.org',
    'address': '164 N State St'
}


def scrape_siskel():
    """Scrape Gene Siskel Film Center schedule using Playwright."""
    movies = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("Playwright not installed - skipping Siskel")
        return movies

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Go to the calendar page
            page.goto(f"{THEATER_INFO['url']}/playing-this-month", timeout=30000)

            # Wait for content to load
            page.wait_for_timeout(5000)

            # Get the page content
            content = page.content()
            browser.close()

    except Exception as e:
        logger.error(f"Playwright error for Siskel: {e}")
        return movies

    # Parse the rendered HTML
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(content, 'lxml')

    current_year = datetime.now().year
    current_month = datetime.now().month

    # Find the calendar view
    calendar = soup.find(class_='view-monthly-calendar')
    if not calendar:
        logger.warning("Siskel: Could not find calendar view")
        return movies

    # Find all day containers
    days = calendar.find_all(class_='calendar-view-day')

    for day in days:
        # Get the day number
        time_elem = day.find(class_='calendar-view-day__number')
        if not time_elem:
            continue

        day_num = time_elem.get_text(strip=True)
        if not day_num.isdigit():
            continue

        day_num = int(day_num)

        # Build the date
        try:
            date = datetime(current_year, current_month, day_num)
            date_str = date.strftime('%Y-%m-%d')
        except ValueError:
            continue

        # Get the films list
        rows = day.find(class_='calendar-view-day__rows')
        if not rows:
            continue

        # Each li contains a film
        for li in rows.find_all('li'):
            # Get the link and title
            link = li.find('a')
            if not link:
                continue

            title = link.get_text(strip=True)
            href = link.get('href', '')

            if not title or len(title) < 2:
                continue

            # Skip navigation items
            if 'next month' in title.lower():
                continue

            title = clean_text(title)

            # Convert from ALL CAPS to Title Case
            if title.isupper():
                title = title.title()

            # Try to find the time - usually in a sibling or nearby element
            time_text = None
            li_text = li.get_text()
            time_match = re.search(r'(\d{1,2}:\d{2}\s*[ap]m)', li_text, re.IGNORECASE)
            if time_match:
                time_text = time_match.group(1)

            # Build ticket URL
            ticket_url = f"{THEATER_INFO['url']}{href}" if href.startswith('/') else href
            if not ticket_url:
                ticket_url = f"{THEATER_INFO['url']}/playing-this-month"

            movies.append({
                'title': title,
                'theater': THEATER_INFO['name'],
                'theater_url': THEATER_INFO['url'],
                'address': THEATER_INFO['address'],
                'date': date_str,
                'times': [time_text] if time_text else ['See website'],
                'format': None,
                'director': None,
                'year': None,
                'ticket_url': ticket_url
            })

    logger.info(f"Gene Siskel: Found {len(movies)} screenings")
    return movies


if __name__ == '__main__':
    results = scrape_siskel()
    for m in results:
        print(f"{m['date']} - {m['title']} @ {m['times']}")
