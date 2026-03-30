import os
import json
import requests
from dotenv import load_dotenv
from apify_client import ApifyClient

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")

if not APIFY_API_TOKEN:
    raise ValueError("APIFY_API_TOKEN not found in .env")

client = ApifyClient(APIFY_API_TOKEN)

# Search for the right actor
print("Searching for the correct LinkedIn Jobs Scraper actor...")
resp = requests.get("https://api.apify.com/v2/store/actors?search=linkedin%20jobs")
if resp.status_code == 200:
    items = resp.json().get('data', {}).get('items', [])
    if not items:
        raise ValueError("No linkedin job scrapers found!")
    # Pick the most popular or relevant one
    actor_id = items[0]['name']
    print(f"Found actor: {actor_id}")
else:
    raise ValueError("Failed to search Apify store")

run_input = {
    "keyword": "receptionist",
    "location": "United States",
    "limit": 5,
    "maxJobs": 5
}

print(f"Starting actor {actor_id}...")
try:
    # Run the Actor and wait for it to finish
    run = client.actor(actor_id).call(run_input=run_input)
    
    print("Fetching results...")
    # Fetch and print Actor results from the run's dataset (if there are any)
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)
        
    os.makedirs(".tmp", exist_ok=True)
    with open(".tmp/jobs.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Successfully saved {len(results)} jobs to .tmp/jobs.json")
except Exception as e:
    print(f"Error: {e}")
