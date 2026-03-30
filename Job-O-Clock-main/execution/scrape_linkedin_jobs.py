import os
import math
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from apify_client import ApifyClient
from composio import Composio

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
COMPOSIO_KEY    = os.getenv("COMPOSIO_API_KEY")
USER_ID         = os.getenv("COMPOSIO_USER_ID")
RECIPIENT       = os.getenv("RECIPIENT_EMAIL")

if not APIFY_API_TOKEN:
    print("Error: APIFY_API_TOKEN not found")
    exit(1)
if not RECIPIENT:
    print("Error: RECIPIENT_EMAIL not found")
    exit(1)
if not COMPOSIO_KEY or not USER_ID:
    print("Error: COMPOSIO_API_KEY or COMPOSIO_USER_ID not found")
    exit(1)

# Run time is noon EST = 17:00 UTC
EST = timezone(timedelta(hours=-5))
run_time = datetime.now(EST).replace(hour=12, minute=0, second=0, microsecond=0)

client   = ApifyClient(APIFY_API_TOKEN)
composio = Composio(api_key=COMPOSIO_KEY)

actor_id = "happitap/linkedin-job-scraper"
keywords = ["investment banking analyst", "mergers and acquisitions analyst"]

run_input = {
    "keywords": keywords,
    "location": "United States",
    "datePosted": "1d",
    "proxyCountry": "US",
    "maxItems": 100
}

print(f"Starting actor {actor_id} with keywords: {keywords}")

try:
    run    = client.actor(actor_id).call(run_input=run_input)
    print("Fetching results...")

    jobs = {}

    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        title       = item.get("title", item.get("jobTitle", ""))
        title_lower = title.lower()

        if "analyst" not in title_lower:
            continue
        if "associate" in title_lower:
            continue

        url = item.get("url", item.get("jobUrl", ""))
        if not url or url in jobs:
            continue

        company    = item.get("company", item.get("companyName", ""))
        location   = item.get("location", "")
        posted_raw = item.get("postedAt", item.get("listDate", ""))

        # Parse posted time and calculate hours ago from noon EST
        posted_dt    = None
        hours_ago_str = "?"
        excel_dt_str  = ""

        if posted_raw:
            try:
                posted_dt = datetime.fromisoformat(str(posted_raw).replace("Z", "+00:00"))
                posted_dt = posted_dt.astimezone(EST)
                excel_dt_str = posted_dt.strftime("%Y-%m-%d %H:%M")
                diff_hours = (run_time - posted_dt).total_seconds() / 3600
                diff_hours = max(0, diff_hours)
                hours_ago_str = "< 1h ago" if diff_hours < 1 else f"{math.floor(diff_hours)}h ago"
            except Exception:
                # Apify returned "X hours ago" string instead of datetime
                import re
                match = re.search(r"(\d+)\s*hour", str(posted_raw))
                if match:
                    h = int(match.group(1))
                    posted_dt = run_time - timedelta(hours=h)
                    excel_dt_str = posted_dt.strftime("%Y-%m-%d %H:%M")
                    hours_ago_str = f"{h}h ago"
                else:
                    excel_dt_str = str(posted_raw)
                    hours_ago_str = "?"

        jobs[url] = {
            "title":      title,
            "company":    company,
            "location":   location,
            "url":        url,
            "excel_dt":   excel_dt_str,
            "hours_ago":  hours_ago_str,
        }

    today = run_time.strftime("%B %d, %Y")

    if not jobs:
        html_body = f"""
        <p>No Investment Banking or M&A Analyst jobs found posted in the last 24 hours for {today}.</p>
        """
        subject = f"IB/M&A Jobs — {today} — No results"
    else:
        rows = ""
        for j in jobs.values():
            rows += f"""
            <tr>
                <td style="padding:8px;border:1px solid #ddd;">{j['title']}</td>
                <td style="padding:8px;border:1px solid #ddd;">{j['company']}</td>
                <td style="padding:8px;border:1px solid #ddd;">{j['location']}</td>
                <td style="padding:8px;border:1px solid #ddd;font-family:monospace;">{j['excel_dt']}</td>
                <td style="padding:8px;border:1px solid #ddd;text-align:center;">{j['hours_ago']}</td>
                <td style="padding:8px;border:1px solid #ddd;"><a href="{j['url']}">Apply</a></td>
            </tr>"""

        html_body = f"""
        <h2 style="font-family:Arial,sans-serif;">IB / M&A Analyst Jobs — {today}</h2>
        <p style="font-family:Arial,sans-serif;color:#555;">
            {len(jobs)} job(s) found posted in the last 24 hours. 
            "Posted" column is formatted for Excel (YYYY-MM-DD HH:MM EST). 
            Script ran at 12:00 PM EST.
        </p>
        <table style="border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px;width:100%;">
            <thead>
                <tr style="background:#1a1a2e;color:white;">
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Title</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Company</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Location</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Posted (EST)</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Hours Ago</th>
                    <th style="padding:10px;border:1px solid #ddd;text-align:left;">Link</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        <p style="font-family:Arial,sans-serif;color:#999;font-size:11px;margin-top:20px;">
            To use in Excel: paste the Posted column → format cells as DateTime.
        </p>
        """
        subject = f"IB/M&A Jobs — {today} — {len(jobs)} found"

    print(f"Sending email: {subject}")

    composio.tools.execute(
        "OUTLOOK_SEND_EMAIL",
        user_id=USER_ID,
        arguments={
            "to": RECIPIENT,
            "subject": subject,
            "body": html_body,
            "is_html": True
        },
        dangerously_skip_version_check=True
    )

    print(f"✅ Email sent! {len(jobs)} jobs.")

except Exception as e:
    print(f"Error: {e}")
    exit(1)
