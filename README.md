# LinkedIn Scraper

A lightweight, automated job scraper built to cut through the noise on LinkedIn and surface only the roles that actually matter — Investment Banking Analyst and M&A Analyst positions posted in the last 24 hours, delivered straight to your inbox every day at noon.

---

## What It Does

LinkedIn's job board is a firehose. Search "investment banking analyst" and you'll get financial analysts, data analysts, corporate banking associates, and a dozen other roles that have nothing to do with what you're looking for. This scraper fixes that.

Every day it searches LinkedIn for a curated set of keywords, filters aggressively for relevance, deduplicates across searches, and emails you a clean HTML table with only the jobs worth looking at — company, title, location, and exactly how many hours ago it was posted.

No Apify. No third-party actors. It hits LinkedIn's public job search API directly, the same endpoint the browser uses when you scroll through listings. Each keyword search pages through results 25 at a time, and anything that slips past the keyword filter gets caught by a secondary relevance check before it makes it into the email.

The whole thing runs on GitHub Actions on a schedule, so once it's set up you don't touch it — it just runs.

---

## Keywords Searched

- `investment banking analyst`
- `mergers and acquisitions analyst`

Results from both searches are deduplicated by URL, so the same listing never appears twice.

---

## What You Get in the Email

Each job in the daily digest includes:

| Field | Example |
|---|---|
| Company | Moelis & Company |
| Title | Investment Banking Analyst, Technology |
| Location | New York, NY |
| Posted | 2h ago |

Jobs are sorted by recency so the freshest postings are always at the top.

---

## Why This Exists

When you're recruiting for IB roles, timing matters. A lot. Banks and boutiques post analyst positions and close them fast — sometimes within days. Checking LinkedIn manually every morning means you're reactive. This tool makes you proactive, with a consistent daily snapshot of everything new hitting the market before you've had your coffee.

It's also just cleaner than LinkedIn's own alerts, which have a habit of surfacing vaguely related roles or notifying you hours after the fact.

---

## Setup

You'll need Python 3.8+ and a free Apify API token — get one at [console.apify.com/account/integrations](https://console.apify.com/account/integrations).

**1. Clone the repo**
```bash
git clone https://github.com/Metdez/Job-O-Clock.git
cd Job-O-Clock
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your API key**

Create a `.env` file in the project root:
```
APIFY_API_TOKEN=YOUR_API_KEY_HERE
```

**4. Run it**
```bash
python execution/scrape_linkedin_jobs.py
```

Results are saved to `.tmp/jobs.json`.

### What You Need

| Requirement | Details |
|---|---|
| Python | 3.8+ |
| Apify API Token | Free tier works — [get one here](https://console.apify.com/account/integrations) |
| Dependencies | `apify-client`, `python-dotenv`, `pandas` |

---

## Tech Stack

- **Python** — core scraping and filtering logic
- **Apify** — LinkedIn job scraper actor (`happitap/linkedin-job-scraper`)
- **GitHub Actions** — daily scheduling at noon EDT
- **Composio + Outlook** — email delivery

---

## Notes

- The 24-hour filter is applied at the Apify actor level, so only fresh postings ever come through.
- Run time is hardcoded to noon EST in the email output — "hours ago" values are calculated relative to that, so they're accurate when GitHub Actions fires the scheduled run.
- Results are cached locally to `.tmp/jobs.json` after each run.
