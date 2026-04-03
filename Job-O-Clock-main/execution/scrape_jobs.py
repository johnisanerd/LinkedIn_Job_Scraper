import os
import math
import re
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from apify_client import ApifyClient
from composio import Composio

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
COMPOSIO_KEY    = os.getenv("COMPOSIO_API_KEY")
USER_ID         = os.getenv("COMPOSIO_USER_ID")
RECIPIENT       = os.getenv("RECIPIENT_EMAIL")

if not APIFY_API_TOKEN:
    print("Error: APIFY_API_TOKEN not found"); exit(1)
if not RECIPIENT:
    print("Error: RECIPIENT_EMAIL not found"); exit(1)
if not COMPOSIO_KEY or not USER_ID:
    print("Error: COMPOSIO_API_KEY or COMPOSIO_USER_ID not found"); exit(1)

EST      = timezone(timedelta(hours=-5))
run_time = datetime.now(EST).replace(hour=12, minute=0, second=0, microsecond=0)
client   = ApifyClient(APIFY_API_TOKEN)
composio = Composio(api_key=COMPOSIO_KEY)

KEYWORDS = ["investment banking analyst", "mergers and acquisitions analyst"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_posted(posted_raw):
    """Return (excel_dt_str, hours_ago_str) from whatever Apify gives us."""
    if not posted_raw:
        return "", "?"
    try:
        posted_dt = datetime.fromisoformat(str(posted_raw).replace("Z", "+00:00"))
        posted_dt = posted_dt.astimezone(EST)
        excel_dt_str  = posted_dt.strftime("%Y-%m-%d %H:%M")
        diff_hours    = max(0, (run_time - posted_dt).total_seconds() / 3600)
        hours_ago_str = "< 1h ago" if diff_hours < 1 else f"{math.floor(diff_hours)}h ago"
        return excel_dt_str, hours_ago_str
    except Exception:
        match = re.search(r"(\d+)\s*hour", str(posted_raw))
        if match:
            h         = int(match.group(1))
            posted_dt = run_time - timedelta(hours=h)
            return posted_dt.strftime("%Y-%m-%d %H:%M"), f"{h}h ago"
        match_days = re.search(r"(\d+)\s*day", str(posted_raw))
        if match_days:
            d         = int(match_days.group(1))
            posted_dt = run_time - timedelta(days=d)
            return posted_dt.strftime("%Y-%m-%d %H:%M"), f"{d}d ago"
        return str(posted_raw), "?"


def is_relevant(title):
    t = title.lower()
    return "analyst" in t and "associate" not in t


def make_job(title, company, location, url, posted_raw, source):
    excel_dt, hours_ago = parse_posted(posted_raw)
    return {
        "title":     title,
        "company":   company,
        "location":  location,
        "url":       url,
        "excel_dt":  excel_dt,
        "hours_ago": hours_ago,
        "source":    source,
    }


# ---------------------------------------------------------------------------
# Scrapers (each returns a dict keyed by URL)
# ---------------------------------------------------------------------------

def scrape_linkedin():
    source  = "LI"
    actor   = "happitap/linkedin-job-scraper"
    run_inp = {
        "keywords":    KEYWORDS,
        "location":    "United States",
        "datePosted":  "1d",
        "proxyCountry": "US",
        "maxItems":    100,
    }
    print(f"[{source}] Starting actor {actor}")
    jobs = {}
    run  = client.actor(actor).call(run_input=run_inp)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        title = item.get("title", item.get("jobTitle", ""))
        if not is_relevant(title):
            continue
        url = item.get("url", item.get("jobUrl", ""))
        if not url or url in jobs:
            continue
        jobs[url] = make_job(
            title,
            item.get("company", item.get("companyName", "")),
            item.get("location", ""),
            url,
            item.get("postedAt", item.get("listDate", "")),
            source,
        )
    print(f"[{source}] {len(jobs)} jobs found")
    return jobs


def scrape_indeed():
    source  = "IN"
    actor   = "shahidirfan/Indeed-Job-Scraper"
    run_inp = {
        "queries":   KEYWORDS,
        "location":  "United States",
        "maxItems":  100,
        "datePosted": "last24Hours",
    }
    print(f"[{source}] Starting actor {actor}")
    jobs = {}
    run  = client.actor(actor).call(run_input=run_inp)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        title = item.get("title", item.get("jobTitle", ""))
        if not is_relevant(title):
            continue
        url = item.get("url", item.get("jobUrl", item.get("externalApplyLink", "")))
        if not url or url in jobs:
            continue
        jobs[url] = make_job(
            title,
            item.get("company", item.get("companyName", "")),
            item.get("location", ""),
            url,
            item.get("postedAt", item.get("date", item.get("postingDateParsed", ""))),
            source,
        )
    print(f"[{source}] {len(jobs)} jobs found")
    return jobs


def scrape_career_pages():
    source  = "CP"
    actor   = "canadesk/career-scraper"
    run_inp = {
        "queries":  KEYWORDS,
        "country":  "United States",
        "maxItems": 100,
    }
    print(f"[{source}] Starting actor {actor}")
    jobs = {}
    run  = client.actor(actor).call(run_input=run_inp)
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        title = item.get("title", item.get("jobTitle", item.get("position", "")))
        if not is_relevant(title):
            continue
        url = item.get("url", item.get("jobUrl", item.get("link", "")))
        if not url or url in jobs:
            continue
        jobs[url] = make_job(
            title,
            item.get("company", item.get("companyName", item.get("employer", ""))),
            item.get("location", ""),
            url,
            item.get("postedAt", item.get("datePosted", item.get("date", ""))),
            source,
        )
    print(f"[{source}] {len(jobs)} jobs found")
    return jobs


# ---------------------------------------------------------------------------
# Run all scrapers in parallel
# ---------------------------------------------------------------------------

scrapers = {
    "LinkedIn":     scrape_linkedin,
    "Indeed":       scrape_indeed,
    "CareerPages":  scrape_career_pages,
}

all_jobs   = {}   # deduplicated by URL
errors     = []   # sources that failed

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {executor.submit(fn): name for name, fn in scrapers.items()}
    for future in as_completed(futures):
        name = futures[future]
        try:
            result = future.result()
            for url, job in result.items():
                if url not in all_jobs:   # first source wins on duplicates
                    all_jobs[url] = job
        except Exception as e:
            print(f"[{name}] ERROR: {e}")
            errors.append(name)

print(f"\nTotal unique jobs after deduplication: {len(all_jobs)}")

# ---------------------------------------------------------------------------
# Build & send email
# ---------------------------------------------------------------------------

today = run_time.strftime("%B %d, %Y")

SOURCE_LABELS = {"LI": "LI", "IN": "IN", "CP": "CP"}
SOURCE_COLORS = {
    "LI": "#0077b5",   # LinkedIn blue
    "IN": "#2164f3",   # Indeed blue
    "CP": "#2e7d32",   # Green for career pages
}

error_banner = ""
if errors:
    error_banner = f"""
    <p style="font-family:Arial,sans-serif;color:#b71c1c;background:#ffebee;
              padding:8px 12px;border-radius:4px;font-size:12px;">
        ⚠️ The following sources encountered errors and may be incomplete: {", ".join(errors)}
    </p>"""

if not all_jobs:
    html_body = f"""
    {error_banner}
    <p style="font-family:Arial,sans-serif;">
        No Investment Banking or M&A Analyst jobs found posted in the last 24 hours for {today}.
    </p>"""
    subject = f"IB/M&A Jobs — {today} — No results"
else:
    rows = ""
    for j in sorted(all_jobs.values(), key=lambda x: x["hours_ago"]):
        badge_color = SOURCE_COLORS.get(j["source"], "#555")
        badge = (
            f'<span style="background:{badge_color};color:white;'
            f'padding:2px 6px;border-radius:3px;font-size:11px;'
            f'font-weight:bold;font-family:monospace;">'
            f'{j["source"]}</span>'
        )
        rows += f"""
        <tr>
            <td style="padding:8px;border:1px solid #ddd;">{j['title']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{j['company']}</td>
            <td style="padding:8px;border:1px solid #ddd;">{j['location']}</td>
            <td style="padding:8px;border:1px solid #ddd;font-family:monospace;">{j['excel_dt']}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">{j['hours_ago']}</td>
            <td style="padding:8px;border:1px solid #ddd;text-align:center;">{badge}</td>
            <td style="padding:8px;border:1px solid #ddd;"><a href="{j['url']}">Apply</a></td>
        </tr>"""

    sources_ok = [n for n in scrapers if n not in errors]
    html_body = f"""
    <h2 style="font-family:Arial,sans-serif;">IB / M&A Analyst Jobs — {today}</h2>
    {error_banner}
    <p style="font-family:Arial,sans-serif;color:#555;">
        {len(all_jobs)} unique job(s) found in the last 24 hours across {", ".join(sources_ok)}.
        "Posted" column is formatted for Excel (YYYY-MM-DD HH:MM EST).
        Script ran at 12:00 PM EST.
    </p>
    <p style="font-family:Arial,sans-serif;color:#555;font-size:12px;">
        Source key: &nbsp;
        <span style="background:#0077b5;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:bold;font-family:monospace;">LI</span> LinkedIn &nbsp;
        <span style="background:#2164f3;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:bold;font-family:monospace;">IN</span> Indeed &nbsp;
        <span style="background:#2e7d32;color:white;padding:2px 6px;border-radius:3px;font-size:11px;font-weight:bold;font-family:monospace;">CP</span> Career Pages
    </p>
    <table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px;width:100%;">
        <thead>
            <tr style="background:#1a1a2e;color:white;">
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Title</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Company</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Location</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Posted (EST)</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Hours Ago</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Src</th>
                <th style="padding:10px;border:1px solid #ddd;text-align:left;">Link</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    <p style="font-family:Arial,sans-serif;color:#999;font-size:11px;margin-top:20px;">
        To use in Excel: paste the Posted column → format cells as DateTime.
    </p>"""
    subject = f"IB/M&A Jobs — {today} — {len(all_jobs)} found"

print(f"Sending email: {subject}")

composio.tools.execute(
    "OUTLOOK_SEND_EMAIL",
    user_id=USER_ID,
    arguments={
        "to":      RECIPIENT,
        "subject": subject,
        "body":    html_body,
        "is_html": True,
    },
    dangerously_skip_version_check=True,
)

print(f"✅ Email sent! {len(all_jobs)} unique jobs from {len(scrapers) - len(errors)}/{len(scrapers)} sources.")
