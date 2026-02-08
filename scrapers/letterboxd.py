"""Fetch movie details from Letterboxd."""
import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path
from .utils import logger

CACHE_FILE = Path(__file__).parent.parent / 'data' / 'letterboxd_cache.json'


def load_cache():
    """Load cached Letterboxd data."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}


def save_cache(cache):
    """Save Letterboxd cache."""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def clean_title(title):
    """Clean title for better matching."""
    # Remove year in parentheses
    title = re.sub(r'\s*\(\d{4}\)\s*', '', title)
    # Remove subtitle after colon or slash (but keep main title)
    # e.g., "Film: A Subtitle" -> "Film"
    if ':' in title:
        title = title.split(':')[0].strip()
    return title


def title_to_slug(title):
    """Convert movie title to Letterboxd URL slug."""
    title = clean_title(title)
    # Convert to lowercase, replace spaces with hyphens
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
    slug = re.sub(r'\s+', '-', slug)  # Spaces to hyphens
    slug = re.sub(r'-+', '-', slug)  # Multiple hyphens to single
    slug = slug.strip('-')
    return slug


def extract_year_from_page(soup):
    """Extract year from Letterboxd page."""
    # Look for year in the page
    # Usually in a link like /films/year/2004/
    year_link = soup.find('a', href=lambda x: x and '/films/year/' in x)
    if year_link:
        match = re.search(r'/films/year/(\d{4})/', year_link.get('href', ''))
        if match:
            return int(match.group(1))

    # Also check the title which often includes year
    title_elem = soup.find('title')
    if title_elem:
        match = re.search(r'\((\d{4})\)', title_elem.get_text())
        if match:
            return int(match.group(1))

    return None


def try_fetch_url(url, headers):
    """Try to fetch a URL and return soup if successful."""
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            return BeautifulSoup(resp.text, 'lxml'), url
    except:
        pass
    return None, None


def fetch_letterboxd_info(title, year=None):
    """Fetch movie info from Letterboxd."""
    cache = load_cache()

    cache_key = f"{title}|{year}" if year else title
    if cache_key in cache:
        return cache[cache_key]

    slug = title_to_slug(title)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

    soup = None
    url = None

    # Strategy: Try with year first if available (more specific)
    if year:
        url_with_year = f'https://letterboxd.com/film/{slug}-{year}/'
        soup, url = try_fetch_url(url_with_year, headers)

    # If year lookup failed, try without year
    if not soup:
        url_no_year = f'https://letterboxd.com/film/{slug}/'
        soup, url = try_fetch_url(url_no_year, headers)

        # Verify the year matches if we got a result and have a target year
        if soup and year:
            page_year = extract_year_from_page(soup)
            if page_year and page_year != year:
                # Wrong year - try some variations
                # Sometimes Letterboxd uses different slug formats
                variations = [
                    f'https://letterboxd.com/film/the-{slug}-{year}/',  # Add "the"
                    f'https://letterboxd.com/film/{slug.replace("the-", "")}-{year}/',  # Remove "the"
                ]
                for var_url in variations:
                    var_soup, var_url_result = try_fetch_url(var_url, headers)
                    if var_soup:
                        var_year = extract_year_from_page(var_soup)
                        if var_year == year:
                            soup, url = var_soup, var_url_result
                            break

                # If still wrong year, skip this match
                if soup:
                    page_year = extract_year_from_page(soup)
                    if page_year and page_year != year:
                        logger.warning(f"Letterboxd year mismatch for {title}: wanted {year}, got {page_year}")
                        cache[cache_key] = None
                        save_cache(cache)
                        return None

    if not soup:
        cache[cache_key] = None
        save_cache(cache)
        return None

    info = {
        'letterboxd_url': url,
        'title': None,
        'director': None,
        'rating': None,
        'tagline': None,
        'description': None,
        'poster': None
    }

    # Title
    title_elem = soup.find('h1', class_='headline-1')
    if title_elem:
        info['title'] = title_elem.get_text(strip=True)

    # Director
    director = soup.find('a', href=lambda x: x and '/director/' in x)
    if director:
        info['director'] = director.get_text(strip=True)

    # Rating (from meta tag)
    rating = soup.find('meta', {'name': 'twitter:data2'})
    if rating:
        rating_text = rating.get('content', '')
        match = re.search(r'([\d.]+)', rating_text)
        if match:
            info['rating'] = match.group(1)

    # Tagline
    tagline = soup.find('h4', class_='tagline')
    if tagline:
        info['tagline'] = tagline.get_text(strip=True)

    # Description
    desc = soup.find('div', class_='truncate')
    if desc:
        info['description'] = desc.get_text(strip=True)[:200]

    # Poster
    poster_div = soup.find('div', class_='film-poster')
    if poster_div:
        img = poster_div.find('img')
        if img and img.get('src'):
            info['poster'] = img.get('src')

    cache[cache_key] = info
    save_cache(cache)
    return info


def enrich_movies_with_letterboxd(movies):
    """Add Letterboxd info to movies list."""
    # Get unique titles with years
    unique_titles = {}
    for movie in movies:
        key = f"{movie['title']}|{movie.get('year', '')}"
        if key not in unique_titles:
            unique_titles[key] = (movie['title'], movie.get('year'))

    # Fetch info for each unique title
    logger.info(f"Fetching Letterboxd info for {len(unique_titles)} unique films...")
    title_info = {}
    for key, (title, year) in unique_titles.items():
        info = fetch_letterboxd_info(title, year)
        if info:
            title_info[key] = info

    logger.info(f"Found Letterboxd data for {len(title_info)} films")

    # Add info to movies
    for movie in movies:
        key = f"{movie['title']}|{movie.get('year', '')}"
        info = title_info.get(key)
        if info:
            movie['letterboxd'] = info

    return movies
