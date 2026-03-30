# Job-O-Clock Setup

Copy and paste this entire prompt into any AI coding assistant (Claude Code, Cursor, Gemini, etc.) to set up the project. Replace `YOUR_API_KEY_HERE` with your actual Apify API token.

---

## Setup Prompt

```
Set up the Job-O-Clock LinkedIn job scraper project. Do the following steps in order:

1. Install Python dependencies:
   pip install apify-client python-dotenv pandas

2. Create a `.env` file in the project root with this content:
   APIFY_API_TOKEN=YOUR_API_KEY_HERE

3. Create the `.tmp/` directory if it doesn't exist.

4. Run the scraper:
   python execution/scrape_linkedin_jobs.py

The script searches LinkedIn for job postings via the Apify API and saves results to `.tmp/jobs.json`.

That's it. The only thing the user needs to provide is their Apify API token.
```

---

## Manual Setup (if not using an AI assistant)

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Metdez/Job-O-Clock.git
   cd Job-O-Clock
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Add your API key:**
   Create a file called `.env` in the project root:
   ```
   APIFY_API_TOKEN=YOUR_API_KEY_HERE
   ```
   Get a free Apify API token at https://console.apify.com/account/integrations

4. **Run it:**
   ```bash
   python execution/scrape_linkedin_jobs.py
   ```

5. **Results** are saved to `.tmp/jobs.json`.

---

## What You Need

| Requirement | Details |
|---|---|
| Python | 3.8+ |
| Apify API Token | Free tier works. Get one at https://console.apify.com/account/integrations |
| Dependencies | `apify-client`, `python-dotenv`, `pandas` (installed via `pip install -r requirements.txt`) |
