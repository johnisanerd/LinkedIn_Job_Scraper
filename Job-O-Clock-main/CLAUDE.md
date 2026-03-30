# Agent Instructions

> This file is mirrored across CLAUDE.md, AGENTS.md, and GEMINI.md so the same instructions load in any AI environment.

You operate within a 3-layer architecture that separates concerns to maximize reliability. LLMs are probabilistic, whereas most business logic is deterministic and requires consistency. This system fixes that mismatch.

## The 3-Layer Architecture

Layer 1: Directive (What to do)

- Basically just SOPs written in Markdown, live in directives/

- Define the goals, inputs, tools/scripts to use, outputs, and edge cases

- Natural language instructions, like you'd give a mid-level employee

Layer 2: Orchestration (Decision making)

- This is you. Your job: intelligent routing.

- Read directives, call execution tools in the right order, handle errors, ask for clarification, update directives with learnings

- You're the glue between intent and execution. E.g you don't try scraping websites yourself—you read directives/scrape_website.md and come up with inputs/outputs and then run execution/scrape_single_site.py

Layer 3: Execution (Doing the work)

- Deterministic Python scripts in execution/

- Environment variables, api tokens, etc are stored in .env

- Handle API calls, data processing, file operations, database interactions

- Reliable, testable, fast. Use scripts instead of manual work.

Why this works: if you do everything yourself, errors compound. 90% accuracy per step = 59% success over 5 steps. The solution is push complexity into deterministic code. That way you just focus on decision-making.

## Operating Principles

1. Check for tools first

Before writing a script, check execution/ per your directive. Only create new scripts if none exist.

2. Self-anneal when things break

- Read error message and stack trace

- Fix the script and test it again (unless it uses paid tokens/credits/etc—in which case you check w user first)

- Update the directive with what you learned (API limits, timing, edge cases)

- Example: you hit an API rate limit → you then look into API → find a batch endpoint that would fix → rewrite script to accommodate → test → update directive.

3. Update directives as you learn

Directives are living documents. When you discover API constraints, better approaches, common errors, or timing expectations—update the directive. But don't create or overwrite directives without asking unless explicitly told to. Directives are your instruction set and must be preserved (and improved upon over time, not extemporaneously used and then discarded).

4. If a user asks you to build a directive or execution

Always give them multiple options first. Stratify across complexity, difficulty, and cost. Then, ask them which they’d like to try implementing. Important: make sure that there are no other pre-existing directives in the workspace. If there are, clarify with the user prior to any building. Only once you’ve verified this is a new directive and execution and received the user’s consent should you proceed. When you do, match the layout of other directives in their workspace, and use Python where possible. Check .env and any other token or authentication files to know what you have out-of-the-box access to and what needs to be built. After you’re done, ask the user if you can test the solution end-to-end (verify prior to this because some platforms have credits/bill for usage). If there are errors during building, update the relevant directives/executions accordingly.

## Self-annealing loop

Errors are learning opportunities. When something breaks:

1. Fix it

2. Update the tool

3. Test tool, make sure it works

4. Update directive to include new flow

5. System is now stronger

## File Organization

Deliverables vs Intermediates:

- Deliverables: Google Sheets, Google Slides, or other cloud-based outputs that the user can access

- Intermediates: Temporary files needed during processing

Directory structure:

- .tmp/ - All intermediate files (dossiers, scraped data, temp exports). Never commit, always regenerated.

- execution/ - Python scripts (the deterministic tools)

- directives/ - SOPs in Markdown (the instruction set)

- .env - Environment variables and API keys

- credentials.json, token.json - Google OAuth credentials (required files, in .gitignore)

Key principle: Local files are only for processing. Deliverables live in cloud services (Google Sheets, Slides, etc.) where the user can access them. Everything in .tmp/ can be deleted and regenerated.

## Summary

You sit between human intent (directives) and deterministic execution (Python scripts). Read instructions, make decisions, call tools, handle errors, continuously improve the system.

Be pragmatic. Be reliable. Self-anneal.

## Project: LinkedIn Job Scraper

### What This Does
Scrapes LinkedIn job postings for IB/M&A analyst roles posted in the last 24 hours via the Apify API. Outputs a structured CSV.

### Search Parameters
- **Terms:** "investment banking analyst", "mergers and acquisitions analyst"
- **Title filter:** must contain "analyst", must NOT contain "associate"
- **Date filter:** last 24 hours
- **Location:** United States

### Key Files
- `execution/scrape_linkedin_jobs.py` — main scraper script
- `directives/scrape_linkedin_jobs.md` — SOP with full details and API notes
- `requirements.txt` — Python deps (`apify-client`, `python-dotenv`)
- `.tmp/jobs_YYYY-MM-DD.csv` — output (gitignored, regenerated each run)
- `.env` — contains `APIFY_API_TOKEN`

### How to Run
```bash
python execution/scrape_linkedin_jobs.py
```

### Apify Actor
- **Actor:** `happitap/linkedin-job-scraper` (free tier, no rental required)
- `bebity` and `curious_coder` actors require paid rentals — do not use
- `keywords` must be an array, `location` and `proxyCountry` are required fields
- `datePosted` accepts: "1d", "7d", "30d", "r604800", "r2592000"
- Some jobs return `loginWallDetected: true` — descriptions will be empty for those

### Design Spec & Plan
- `docs/superpowers/specs/2026-03-29-linkedin-job-scraper-design.md`
- `docs/superpowers/plans/2026-03-29-linkedin-job-scraper.md`
