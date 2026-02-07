# Chicago Art House Cinema

A website showing weekly movie schedules from Chicago's independent and repertory theaters.

**Live site:** https://astagoff2.github.io/chicago-arthouse-movies/

## Theaters

| Theater | Source | Method |
|---------|--------|--------|
| Gene Siskel Film Center | siskelfilmcenter.org | Playwright (JS-rendered calendar) |
| Doc Films | docfilms.org | HTML parsing |
| Music Box Theatre | musicboxtheatre.com | HTML parsing |
| Logan Theatre | thelogantheatre.com | HTML parsing |
| Facets Cinematheque | facets.org | HTML parsing |
| Alamo Drafthouse Wrigleyville | drafthouse.com | JSON API |

## How It Works

1. **Scraping**: Python scripts fetch showtimes from each theater's website. Most use BeautifulSoup for HTML parsing; Siskel requires Playwright for JavaScript-rendered content; Alamo uses their internal JSON API.

2. **Data Pipeline**: All scrapers output a unified format with title, theater, date, times, and ticket URLs. Results are merged and filtered to the current week.

3. **Static Generation**: Jinja2 templates render the data into a single HTML page, grouped by date.

4. **Deployment**: GitHub Actions runs the build daily and deploys to GitHub Pages via the `gh-pages` branch.

## Project Structure

```
chicago-arthouse-movies/
├── scrapers/
│   ├── __init__.py
│   ├── siskel.py      # Playwright-based
│   ├── doc_films.py
│   ├── music_box.py
│   ├── logan.py
│   ├── facets.py
│   ├── alamo.py       # API-based
│   └── utils.py       # Shared utilities
├── data/
│   └── movies.json    # Generated schedule
├── site/
│   ├── index.html     # Generated page
│   ├── about.html     # About page
│   └── styles.css
├── templates/
│   └── index_template.html
├── build.py           # Main build script
├── requirements.txt
└── .github/
    └── workflows/
        └── deploy.yml # Daily automation
```

## Data Schema

```json
{
  "title": "Film Title",
  "theater": "Music Box Theatre",
  "theater_url": "https://musicboxtheatre.com",
  "address": "3733 N Southport Ave",
  "date": "2026-02-07",
  "times": ["7:00 PM", "9:30 PM"],
  "format": "35mm",
  "director": "Director Name",
  "year": 2024,
  "ticket_url": "https://..."
}
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# For Siskel scraper (requires Playwright)
playwright install chromium

# Run the build
python build.py

# View the site
open site/index.html
```

## Automated Updates

The site rebuilds daily at 6am Chicago time (12:00 UTC) via GitHub Actions. The workflow:
1. Checks out the repo
2. Installs Python dependencies and Playwright
3. Runs `build.py` to scrape all theaters
4. Deploys the `site/` folder to the `gh-pages` branch

## Tech Stack

- **Scraping**: Python 3, BeautifulSoup4, Playwright
- **Templating**: Jinja2
- **Frontend**: Vanilla HTML/CSS
- **Hosting**: GitHub Pages
- **Automation**: GitHub Actions

## Notes

- Scrapers may break if theaters change their website structure
- Siskel and Alamo typically have the most screenings
- Some theaters don't expose specific showtimes; these show "See website"
- The week filter shows today through 7 days out
