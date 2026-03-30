# LinkedIn Job Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape LinkedIn job postings for IB/M&A analyst roles posted in the last 24 hours and output a structured CSV.

**Architecture:** Single Python script calls the Apify `happitap/linkedin-job-scraper` actor for each search term, merges results, filters to analyst-only titles (excluding associate), deduplicates by URL, and writes a CSV to `.tmp/`. A directive SOP documents the full process.

**Tech Stack:** Python 3, `apify-client`, `python-dotenv`, CSV stdlib

---

## File Structure

| File | Responsibility |
|------|---------------|
| `execution/scrape_linkedin_jobs.py` | Main script — calls Apify, filters, dedupes, writes CSV |
| `directives/scrape_linkedin_jobs.md` | SOP — goals, inputs, edge cases, how to run |
| `requirements.txt` | Python dependencies |
| `.tmp/jobs_YYYY-MM-DD.csv` | Output (gitignored, regenerated each run) |

---

### Task 1: Set Up Python Dependencies

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
apify-client>=1.0.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Install dependencies**

Run: `pip install -r requirements.txt`
Expected: Successfully installed apify-client and python-dotenv

- [ ] **Step 3: Verify .tmp directory exists**

Run: `ls .tmp/`
If missing, create it: `mkdir -p .tmp`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add Python dependencies for LinkedIn scraper"
```

---

### Task 2: Write the Scraper Script

**Files:**
- Create: `execution/scrape_linkedin_jobs.py`

- [ ] **Step 1: Create the scraper script**

```python
import csv
import os
import sys
from datetime import datetime, timezone

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
if not APIFY_TOKEN:
    print("ERROR: APIFY_API_TOKEN not set in .env")
    sys.exit(1)

ACTOR_ID = "happitap/linkedin-job-scraper"

SEARCH_TERMS = [
    "investment banking analyst",
    "mergers and acquisitions analyst",
]

MAX_JOBS_PER_TERM = 100
DATE_POSTED = "1d"
PROXY_COUNTRY = "US"
LOCATION = "United States"

CSV_COLUMNS = [
    "job_id",
    "title",
    "company",
    "company_url",
    "location",
    "url",
    "posted_at",
    "experience_level",
    "employment_type",
    "is_remote",
    "description_snippet",
    "scraped_at",
]


def run_actor(client, keyword):
    """Run the Apify actor for a single search term and return items."""
    print(f"  Searching: '{keyword}'...")
    run_input = {
        "keywords": [keyword],
        "location": LOCATION,
        "maxJobs": MAX_JOBS_PER_TERM,
        "datePosted": DATE_POSTED,
        "proxyCountry": PROXY_COUNTRY,
    }
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"    Found {len(items)} raw results")
    return items


def passes_title_filter(title):
    """Return True if title contains 'analyst' and does NOT contain 'associate'."""
    t = title.lower()
    return "analyst" in t and "associate" not in t


def normalize_item(item):
    """Convert raw Apify output to our CSV schema."""
    return {
        "job_id": item.get("jobId", ""),
        "title": item.get("jobTitle", ""),
        "company": item.get("companyName", ""),
        "company_url": item.get("companyUrl", ""),
        "location": item.get("location", ""),
        "url": item.get("jobUrl", ""),
        "posted_at": item.get("postedAt", ""),
        "experience_level": item.get("experienceLevel", ""),
        "employment_type": item.get("employmentType", ""),
        "is_remote": str(item.get("isRemote", False)),
        "description_snippet": item.get("jobDescription", "")[:200],
        "scraped_at": item.get("scrapedAt", ""),
    }


def main():
    client = ApifyClient(APIFY_TOKEN)
    all_items = []

    print("LinkedIn Job Scraper")
    print("=" * 40)

    for term in SEARCH_TERMS:
        try:
            items = run_actor(client, term)
            all_items.extend(items)
        except Exception as e:
            print(f"  ERROR running actor for '{term}': {e}")
            sys.exit(1)

    # Filter: must have "analyst" in title, must NOT have "associate"
    filtered = [item for item in all_items if passes_title_filter(item.get("jobTitle", ""))]
    print(f"\nAfter title filter (analyst only, no associate): {len(filtered)} jobs")

    # Deduplicate by job URL
    seen_urls = set()
    unique = []
    for item in filtered:
        url = item.get("jobUrl", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique.append(item)
    print(f"After deduplication: {len(unique)} jobs")

    # Normalize and write CSV
    rows = [normalize_item(item) for item in unique]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_path = os.path.join(".tmp", f"jobs_{today}.csv")
    os.makedirs(".tmp", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nOutput: {output_path} ({len(rows)} jobs)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the script has no syntax errors**

Run: `python -c "import py_compile; py_compile.compile('execution/scrape_linkedin_jobs.py', doraise=True)"`
Expected: No output (clean compile)

- [ ] **Step 3: Commit**

```bash
git add execution/scrape_linkedin_jobs.py
git commit -m "feat: add LinkedIn job scraper script using Apify"
```

---

### Task 3: Write the Directive

**Files:**
- Create: `directives/scrape_linkedin_jobs.md`

- [ ] **Step 1: Create the directive SOP**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add directives/scrape_linkedin_jobs.md
git commit -m "docs: add LinkedIn job scraper directive SOP"
```

---

### Task 4: End-to-End Test Run

- [ ] **Step 1: Run the scraper**

Run: `python execution/scrape_linkedin_jobs.py`
Expected: Script prints search progress, filter counts, and writes CSV to `.tmp/jobs_YYYY-MM-DD.csv`

- [ ] **Step 2: Verify CSV output**

Run: `head -5 .tmp/jobs_*.csv`
Expected: CSV header row followed by job data rows with populated fields

- [ ] **Step 3: Verify title filter worked**

Run: `python -c "import csv; r=csv.DictReader(open('.tmp/jobs_$(date +%Y-%m-%d).csv')); [print(row['title']) for row in r]"`
Expected: All titles contain "analyst" (case-insensitive), none contain "associate"

- [ ] **Step 4: If errors, self-anneal**

Fix the script, re-test, update the directive with any learnings.
