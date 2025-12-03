# Integrations for Apify, web scrapers, and related tools will go here.

from dotenv import load_dotenv
import os
import json
from apify_client import ApifyClient

load_dotenv()

APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
if not APIFY_TOKEN:
    raise RuntimeError("APIFY_TOKEN environment variable is not set. Please check your .env file.")

def load_actor_scrapers(json_path: str = None):
    """
    Load actor scraper definitions (with pricing, actor_id, etc) from a JSON file.
    Returns a list of dicts.
    """
    if json_path is None:
        json_path = os.path.join(os.path.dirname(__file__), "actor_scrapers.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_apify_actor(scraper_entry: dict, extra_input: dict = None):
    """
    Run an Apify actor using the configuration from a scraper entry (from actor_scrapers.json).
    Optionally merge in extra_input to override or add to the default input.
    Returns the run object and the scraped items as a list of dicts.
    """
    
    client = ApifyClient(APIFY_TOKEN)
    actor_id = scraper_entry["actor_id"]
    run_input = dict(scraper_entry["input"])  # Copy default input
    if extra_input:
        run_input.update(extra_input)
    run = client.actor(actor_id).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return run, items



