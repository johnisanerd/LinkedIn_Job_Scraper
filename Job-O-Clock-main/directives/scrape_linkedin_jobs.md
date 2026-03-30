# Directive: Scrape LinkedIn Jobs

## Goal
Scrape job postings from LinkedIn using Apify and save the results locally.

## Inputs
- **Actor:** `rockyhq/linkedin-jobs-scraper` (or similar)
- **Search URL / Keyword:** E.g., "receptionist" in "United States"
- **API Key:** `APIFY_API_TOKEN` stored in `.env`

## Execution Script
The orchestration runs `execution/scrape_linkedin_jobs.py`.

## Outputs
- Data saved as JSON in `.tmp/jobs.json`.
- Output includes job title, location, salary, posted time, and company name.

## Edge Cases
- Rate limit handling logic is contained within the Apify platform/actor.
- If actor isn't found or changes, we search Apify Store and update the actor ID in the script.
