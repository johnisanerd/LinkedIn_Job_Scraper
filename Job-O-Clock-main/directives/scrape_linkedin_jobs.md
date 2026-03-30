# Directive: Scrape LinkedIn Jobs

## Goal
Find investment banking and M&A analyst job postings from LinkedIn that were posted in the last 24 hours.

## Inputs
- **Search terms:** "investment banking analyst", "mergers and acquisitions analyst"
- **Date filter:** last 24 hours (`datePosted: "1d"`)
- **Location:** United States
- **Title filter:** must contain "analyst" (case-insensitive), must NOT contain "associate"

## Tools
- **Script:** `execution/scrape_linkedin_jobs.py`
- **API:** Apify actor `happitap/linkedin-job-scraper`
- **Credentials:** `APIFY_API_TOKEN` in `.env`

## How to Run
```bash
cd <project root>
python execution/scrape_linkedin_jobs.py
```

## Output
- CSV file at `.tmp/jobs_YYYY-MM-DD.csv`
- Columns: job_id, title, company, company_url, location, url, posted_at, experience_level, employment_type, is_remote, description_snippet, scraped_at

## Edge Cases
- **No results:** script writes CSV with headers only, prints "0 jobs"
- **Actor failure:** script prints error and exits with code 1
- **Duplicates:** deduplicated by job URL across search terms
- **Missing fields:** empty string used for any field the actor doesn't return
- **"Associate Analyst" titles:** excluded by title filter (contains "associate")

## API Notes (learned from testing)
- Actor: `happitap/linkedin-job-scraper` (free tier, no rental required)
- `keywords` must be an array of strings
- `location` is required (using "United States")
- `datePosted` accepts: "1d", "7d", "30d", "r604800", "r2592000"
- `proxyCountry` is required, must be 2-letter code (using "US")
- Actor returns `loginWallDetected: true` for some jobs — descriptions may be empty
- `dataQuality` field indicates "partial" vs "full" data availability
