"""Shared utilities for scrapers."""
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_week_dates():
    """Get dates for the current week (Mon-Sun)."""
    today = datetime.now()
    # Find Monday of current week
    monday = today - timedelta(days=today.weekday())
    return [(monday + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]


def parse_date(date_str, year=None):
    """Parse various date formats into YYYY-MM-DD."""
    if not date_str:
        return None
    try:
        if year:
            date_str = f"{date_str} {year}"
        parsed = date_parser.parse(date_str, fuzzy=True)
        return parsed.strftime('%Y-%m-%d')
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse date: {date_str} - {e}")
        return None


def parse_time(time_str):
    """Normalize time format to 'H:MM PM' style."""
    if not time_str:
        return None
    time_str = time_str.strip().upper()
    # Handle various formats
    time_str = re.sub(r'(\d{1,2}):(\d{2})\s*(AM|PM)', r'\1:\2 \3', time_str)
    time_str = re.sub(r'(\d{1,2})(AM|PM)', r'\1:00 \2', time_str)
    return time_str


def clean_text(text):
    """Clean up text by removing extra whitespace."""
    if not text:
        return ""
    return ' '.join(text.split())


def make_request(url, session=None, timeout=30, retries=2):
    """Make HTTP request with error handling and retries."""
    import requests
    import time

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for attempt in range(retries + 1):
        try:
            if session:
                resp = session.get(url, headers=headers, timeout=timeout)
            else:
                resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            if attempt < retries:
                time.sleep(2)
                continue
            logger.error(f"Request failed for {url}: {e}")
            return None
