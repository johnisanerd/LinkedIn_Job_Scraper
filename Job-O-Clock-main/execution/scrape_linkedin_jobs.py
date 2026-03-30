import os
import csv
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    print("Error: APIFY_API_TOKEN not found in .env")
    exit(1)

client = ApifyClient(APIFY_API_TOKEN)
actor_id = "happitap/linkedin-job-scraper"
keywords = ["investment banking analyst", "mergers and acquisitions analyst"]

run_input = {
    "keywords": keywords,
    "location": "United States",
    "datePosted": "1d",
    "proxyCountry": "US"
}
# Limiting to avoid mass credits consumption if test
run_input["maxItems"] = 100

print(f"Starting actor {actor_id} with keywords: {keywords}")

try:
    run = client.actor(actor_id).call(run_input=run_input)
    print("Fetching results...")
    
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = f".tmp/jobs_{today}.csv"
    os.makedirs(".tmp", exist_ok=True)
    
    headers = [
        "job_id", "title", "company", "company_url", "location", 
        "url", "posted_at", "experience_level", "employment_type", 
        "is_remote", "description_snippet", "scraped_at"
    ]
    
    jobs = {}
    
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        title = item.get("title", item.get("jobTitle", ""))
        title_lower = title.lower()
        
        # filters
        if "analyst" not in title_lower:
            continue
        if "associate" in title_lower:
            continue
            
        url = item.get("url", item.get("jobUrl", ""))
        if not url:
            continue
            
        if url in jobs:
            continue
            
        job_id = str(item.get("id", item.get("jobId", "")))
        company = item.get("company", item.get("companyName", ""))
        company_url = item.get("companyUrl", item.get("companyLinkedinUrl", ""))
        location = item.get("location", "")
        posted_at = item.get("postedAt", item.get("listDate", ""))
        experience_level = item.get("experienceLevel", item.get("seniorityLevel", ""))
        employment_type = item.get("employmentType", "")
        is_remote = str(item.get("isRemote", item.get("workplaceType", "") == "Remote"))
        description_snippet = item.get("description", item.get("jobDescription", ""))
        scraped_at = datetime.now().isoformat()
        
        jobs[url] = {
            "job_id": job_id,
            "title": title,
            "company": company,
            "company_url": company_url,
            "location": location,
            "url": url,
            "posted_at": posted_at,
            "experience_level": experience_level,
            "employment_type": employment_type,
            "is_remote": is_remote,
            "description_snippet": description_snippet[:200] if description_snippet else "",
            "scraped_at": scraped_at
        }
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for job in jobs.values():
            writer.writerow(job)
            
    if not jobs:
        print("0 jobs found matching criteria.")
    else:
        print(f"Successfully saved {len(jobs)} jobs to {output_file}")
        
except Exception as e:
    print(f"Error: {e}")
    exit(1)
