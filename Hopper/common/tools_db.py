# Functions like save_jobs_to_db, get_jobs, etc. will go here.
import json
from typing import List, Optional, Any, Dict
import sqlite3
from datetime import datetime
import logging

def save_jobs_to_db(jobs, db_path='jobs.db'):
    """
    Save a list of job dicts to a SQLite DB, storing key fields, enrichment fields, and the full JSON blob.
    Accepts jobs from any source (scraper, email, API, etc.).
    Skips duplicates based on (external_id, source).
    Returns a dict with counts: inserted, skipped, failed.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT,
            source TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            salary_text TEXT,
            description TEXT,
            requirements TEXT,
            alert_type TEXT,
            alert_query TEXT,
            received_at TEXT,
            raw_json TEXT,
            UNIQUE (external_id, source)
        )
    ''')
    inserted = 0
    skipped = 0
    failed = 0
    for job in jobs:
        external_id = job.get('id') or job.get('external_id')
        try:
            c.execute('SELECT id FROM jobs WHERE external_id = ? AND source = ?', (external_id, job.get('source')))
            if c.fetchone():
                logging.info(f"[DUPLICATE] Skipping duplicate job: external_id={external_id}, source={job.get('source')}")
                skipped += 1
                continue
            c.execute('''
                INSERT INTO jobs (
                    external_id, source, title, company, location, url, salary_text, description, requirements, alert_type, alert_query, received_at, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                external_id,
                job.get('source'),
                job.get('title'),
                job.get('company'),
                job.get('location'),
                job.get('url'),
                job.get('salary_text'),
                job.get('description'),
                job.get('requirements'),
                job.get('alert_type'),
                job.get('alert_query'),
                job.get('received_at') if job.get('received_at') else None,
                json.dumps(job)
            ))
            inserted += 1
        except Exception as e:
            logging.error(f"[ERROR] Failed to insert job: external_id={external_id}, source={job.get('source')}, error={e}")
            failed += 1
            continue
    conn.commit()
    conn.close()
    logging.info(f"[DB SAVE SUMMARY] Inserted: {inserted}, Skipped (duplicates): {skipped}, Failed: {failed}")
    return {"inserted": inserted, "skipped": skipped, "failed": failed}

# Example dataclass for reference (not required for DB, but useful for validation and enrichment)
from dataclasses import dataclass, field

@dataclass
class JobPosting:
    id: Optional[int] = None
    source: str = ""
    title: str = ""
    company: str = ""
    location: Optional[str] = None
    url: Optional[str] = None
    salary_text: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    alert_type: Optional[str] = None
    alert_query: Optional[str] = None
    received_at: Optional[datetime] = None
    raw_payload: Optional[Dict[str, Any]] = field(default_factory=dict)

# TODO: Add more helper functions as needed for enrichment, updating, and querying jobs.
