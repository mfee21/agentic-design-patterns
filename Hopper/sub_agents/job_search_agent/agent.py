import os
import logging
import time
import sys
from google.adk.agents import Agent
from google.adk.sessions import Session
from google.adk.tools.function_tool import FunctionTool
from common.tools_scrapers import (
    load_actor_scrapers,
    run_apify_actor,
)
from common.tools_db import save_jobs_to_db
from common.gmail_extractor import extract_linkedin_jobs_from_gmail, extract_builtin_jobs_from_gmail

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../common')))
import tools_gmail


# === Logging added Nov 2025 for agent workflow visibility ===
# These logs help track the job search agent's progress and make debugging easier.
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
# === End logging annotation ===


# Define the scraping tool function before wrapping

def run_job_search_and_save_db():
    """
    Runs all built scraper tools (from actor_scrapers.json), skips unbuilt, and saves results to the database.
    Logs progress at each step for transparency and debugging.
    Notifies the user when scraping starts, is waiting, and if still waiting every 2 minutes.
    Returns a summary of DB write results.
    """
    logging.info("[SERIAL EXECUTION] Starting job search: running scraper tools serially...")
    scrapers = load_actor_scrapers()
    results = []
    for scraper in scrapers:
        scraper_label = scraper.get('label', scraper.get('scraper', 'unknown_scraper'))
        urls = scraper['input'].get('urls', [])
        for url_entry in urls:
            url_shortname = url_entry['name']
            url_value = url_entry['url']
            logging.info(f"[SERIAL EXECUTION] Running scraper: {scraper_label} for {url_shortname}...")
            print(f"Hopper: Starting job scraping with {scraper_label} ({url_shortname})...")
            start_time = time.time()
            try:
                print("Hopper: Waiting for results from the scraper. This may take a few minutes...")
                last_wait_log = start_time
                run, items = None, []
                # Pass the single URL as input override
                extra_input = dict(scraper['input'])
                extra_input['urls'] = [url_value]
                while True:
                    run, items = run_apify_actor(scraper, extra_input=extra_input)
                    if items:
                        break
                    elapsed = time.time() - start_time
                    if time.time() - last_wait_log > 120:
                        print(f"Hopper: Still waiting for results... ({int(elapsed // 60)} min {int(elapsed % 60)} sec elapsed)")
                        last_wait_log = time.time()
                    time.sleep(10)
                logging.info(f"[SERIAL EXECUTION] Scraper '{scraper_label}' ({url_shortname}) returned {len(items)} items.")
                # Annotate each job with source and source_url (shortname)
                for job in items:
                    job['source'] = scraper_label
                    job['source_url'] = url_shortname
                results.extend(items)
                logging.info(f"[SERIAL EXECUTION] Finished scraper: {scraper_label} for {url_shortname}.")
            except Exception as e:
                logging.error(f"[SERIAL EXECUTION] Error running scraper '{scraper_label}' ({url_shortname}): {e}")
    if not results:
        logging.warning("[SERIAL EXECUTION] No results found from any scraper.")
        print("Hopper: No results found from any scraper.")
        return "No jobs found from any scraper."
    # Save to database
    logging.info(f"[SERIAL EXECUTION] Saving {len(results)} jobs to the database...")
    print(f"Hopper: Saving {len(results)} jobs to the database...")
    db_result = save_jobs_to_db(results)
    logging.info(f"[SERIAL EXECUTION] Saved {db_result['inserted']} jobs to the database. Skipped: {db_result['skipped']}, Failed: {db_result['failed']}")
    print(f"Hopper: Saved {db_result['inserted']} jobs to the database. Skipped: {db_result['skipped']}, Failed: {db_result['failed']}")
    logging.info("[SERIAL EXECUTION] Finished all scraper tools.")
    return f"Inserted: {db_result['inserted']}, Skipped (duplicates): {db_result['skipped']}, Failed: {db_result['failed']}"
# Now wrap the function as a FunctionTool
run_job_search_and_save_db_tool = FunctionTool(run_job_search_and_save_db)

# --- Granular tool selection logic ---
def run_gmail_linkedin_extraction_and_save_db():
    """
    Extract LinkedIn jobs from Gmail and save to DB. Returns DB save summary.
    """
    logging.info("[SERIAL EXECUTION] Starting Gmail LinkedIn job extraction...")
    result = extract_linkedin_jobs_from_gmail(delete_after_fetch=False, db_path='jobs.db')
    logging.info("[SERIAL EXECUTION] Finished Gmail LinkedIn job extraction.")
    # If the Gmail extractor returns a DB result, use it; otherwise, return a generic message
    if isinstance(result, dict) and all(k in result for k in ("inserted", "skipped", "failed")):
        return f"Inserted: {result['inserted']}, Skipped (duplicates): {result['skipped']}, Failed: {result['failed']}"
    return str(result)

run_gmail_linkedin_extraction_and_save_db_tool = FunctionTool(run_gmail_linkedin_extraction_and_save_db)

# --- Granular tool selection logic ---
def run_gmail_builtin_extraction_and_save_db():
    """
    Extract BuiltIn jobs from Gmail and save to DB. Returns DB save summary.
    """
    logging.info("[SERIAL EXECUTION] Starting Gmail BuiltIn job extraction...")
    result = extract_builtin_jobs_from_gmail(delete_after_fetch=False, db_path='jobs.db')
    logging.info("[SERIAL EXECUTION] Finished Gmail BuiltIn job extraction.")
    if isinstance(result, dict) and all(k in result for k in ("inserted", "skipped", "failed")):
        return f"Inserted: {result['inserted']}, Skipped (duplicates): {result['skipped']}, Failed: {result['failed']}"
    return str(result)

run_gmail_builtin_extraction_and_save_db_tool = FunctionTool(run_gmail_builtin_extraction_and_save_db)

# --- Granular tool selection logic ---
def job_search_agent_router(user_input: str):
    """
    Route to the correct job search tool(s) based on user input.
    """
    lowered = user_input.lower()
    if "builtin" in lowered:
        logging.info("[AGENT ROUTER] User requested Gmail/BuiltIn email extraction only.")
        return run_gmail_builtin_extraction_and_save_db()
    if "gmail" in lowered or "email" in lowered or "linkedin email" in lowered:
        logging.info("[AGENT ROUTER] User requested Gmail/LinkedIn email extraction only.")
        return run_gmail_linkedin_extraction_and_save_db()
    logging.info("[AGENT ROUTER] User requested general job search. Running all tools.")
    return run_job_search_and_save_db()

job_search_agent = Agent(
    name="job_search_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are Hopper, a Job Search Agent.\n"
        "\n"
        "Available functionality (as of now):\n"
        "- Scrape jobs from LinkedIn using built scraper tools (actor_scrapers.json).\n"
        "- Extract jobs from your Gmail job alert emails, including both LinkedIn and BuiltIn alerts.\n"
        "- If the user asks to 'extract builtin emails', you should run the BuiltIn Gmail extraction tool.\n"
        "- All results are saved to the database for inspection.\n"
        "\n"
        "If the user requests a job search, you MUST use only the available built tools. Reply: 'Using available job search tools. Other functionality is not yet built.'\n"
        "If the user requests a job search for an un-built or unsupported source, reply: 'That functionality is not yet built.'\n"
        "If the user requests anything out of scope, reply: 'That functionality is not in my scope.'\n"
        "\n"
        "When the user asks for jobs, you should:\n"
        "1) Use the available job scraping and Gmail extraction tools to collect jobs and save results to the database.\n"
        "2) Return a concise human-readable summary (e.g., top 10 jobs) and a message confirming database save.\n"
        "\n"
        "As new sources and features are built, update your responses to reflect your current capabilities."
    ),
    tools=[
        run_job_search_and_save_db_tool,
        run_gmail_linkedin_extraction_and_save_db_tool,
        run_gmail_builtin_extraction_and_save_db_tool,
    ],
)
