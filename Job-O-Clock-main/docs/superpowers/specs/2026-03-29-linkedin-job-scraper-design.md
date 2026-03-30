# LinkedIn Job Scraper — Design Spec

## Overview

Scrape LinkedIn job postings for investment banking and M&A analyst roles posted within the last 24 hours using the Apify API. Output a structured CSV file.

## Requirements

- **Search terms:** "investment banking analyst", "mergers and acquisitions analyst"
- **Time filter:** posted within last 24 hours
- **Title filter:** must contain "analyst" (case-insensitive); exclude any title containing "associate"
- **Location:** United States (required by actor)
- **Output:** CSV file at `.tmp/jobs_YYYY-MM-DD.csv`

## Architecture

Two files following the 3-layer pattern:

1. `directives/scrape_linkedin_jobs.md` — SOP with goals, inputs, edge cases
2. `execution/scrape_linkedin_jobs.py` — deterministic Python script

### Data Flow

```
Run script
  → Load .env (APIFY_API_TOKEN)
  → Call Apify LinkedIn Jobs actor for each search term
  → Collect raw results
  → Filter: posted within 24h, title contains "analyst", title excludes "associate"
  → Deduplicate by job URL
  → Normalize fields
  → Write CSV to .tmp/jobs_YYYY-MM-DD.csv
  → Print summary (count, file path)
```

## Apify Actor

Use `happitap/linkedin-job-scraper` (free tier, no rental required). The `bebity` and `curious_coder` actors require paid rentals.

### Actor Input

```json
{
  "keywords": ["investment banking analyst"],
  "location": "United States",
  "maxJobs": 100,
  "datePosted": "1d",
  "proxyCountry": "US"
}
```

Run once per search term, then merge results.

### Actor Output Fields

`jobId`, `jobTitle`, `companyName`, `companyUrl`, `location`, `jobUrl`, `postedAt`, `jobDescription`, `employmentType`, `experienceLevel`, `isRemote`, `scrapedAt`, `dataQuality`

Note: `loginWallDetected` may be `true` for some jobs, meaning `jobDescription` will be empty.

## CSV Schema

| Column | Type | Description |
|--------|------|-------------|
| `job_id` | string | LinkedIn job ID |
| `title` | string | Job title |
| `company` | string | Company name |
| `company_url` | string | Company LinkedIn page |
| `location` | string | Job location |
| `url` | string | LinkedIn posting URL |
| `posted_at` | string | When posted (e.g., "15 hours ago") |
| `experience_level` | string | Seniority/YOE if available |
| `employment_type` | string | Full-time, contract, etc. |
| `is_remote` | string | "True" or "False" |
| `description_snippet` | string | First ~200 chars of job description |
| `scraped_at` | string | ISO timestamp of when data was scraped |

## Dependencies

- `apify-client` — Apify Python SDK
- `python-dotenv` — load `.env` variables

## Edge Cases

- **No results:** script prints "No jobs found for [term]" and writes an empty CSV with headers only
- **Duplicate jobs:** deduplicate by `url` field before writing CSV
- **Actor failure:** print error message with actor name and status, exit with code 1
- **Missing fields:** use empty string for any field the actor doesn't return
- **Rate limits:** Apify handles this internally; no retry logic needed in our script
- **Title filtering:** case-insensitive match; "Analyst" and "analyst" both pass; "Associate Analyst" is excluded because it contains "associate"
