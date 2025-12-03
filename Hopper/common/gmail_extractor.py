"""
gmail_extractor.py: Unified interface for Gmail-based job ingestion tools for Hopper agents.
- Provides functions for extracting and storing jobs from various Gmail sources.
- Contains all job-source-specific parsing and ID extraction logic.
- Each function calls the appropriate fetch-and-store logic from tools_gmail.py.
"""
import logging
from .tools_gmail import fetch_job_alert_emails
from .tools_db import save_jobs_to_db
from bs4 import BeautifulSoup
import re
import urllib.parse
import sys

def parse_linkedin_job_alert_email(html: str) -> list:
    """
    Parses LinkedIn job alert HTML and extracts job postings as dicts.
    Assumes each job is in a <tbody> with 3 <tr>s:
      1. <tr>: <a> with job title and URL
      2. <tr>: <td> with company · location
      3. <tr>: (ignored)
    Returns a list of job dicts with title, company, location, url, etc.
    """
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    for tbody in soup.find_all('tbody'):
        trs = tbody.find_all('tr', recursive=False)
        if len(trs) < 2:
            continue  # Not a job block
        # 1. First <tr>: job title and URL
        first_tr = trs[0]
        a_tag = first_tr.find('a', href=True)
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        url = a_tag['href']
        # 2. Second <tr>: company and location
        second_tr = trs[1]
        company = location = None
        td = second_tr.find('td')
        if td:
            text = td.get_text(strip=True)
            parts = [p.strip() for p in text.split('·')]
            if len(parts) == 2:
                company, location = parts
            elif len(parts) == 1:
                company = parts[0]
        # Only add if title and url are present
        if title and url:
            jobs.append({
                'title': title,
                'url': url,
                'company': company,
                'location': location,
                'salary_text': None,
                'source': 'linkedin_email',
                'needs_enrichment': True,
                'raw_html': str(tbody)
            })
    return jobs

def extract_linkedin_job_id(url):
    match = re.search(r'/jobs/view/(\d+)', url)
    if match:
        return match.group(1)
    return url  # fallback to full URL if not matched

def parse_builtin_job_alert_email(html: str) -> list:
    """
    Parses BuiltIn job alert HTML and extracts job postings as dicts.
    Handles redirect/encoded links to extract the real BuiltIn job URL.
    Returns a list of job dicts with title, company, location, salary, url, etc.
    """
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Try to extract the real BuiltIn job URL from redirect/encoded links
        job_url = None
        # 1. Look for URL-encoded builtin.com/job/ links inside the href
        decoded_href = urllib.parse.unquote(href)
        match = re.search(r'(https?://builtin.com/job/[^?\s]+)', decoded_href)
        if match:
            job_url = match.group(1)
        # 2. Fallback: look for encoded job id
        if not job_url:
            match = re.search(r'builtin.com%2Fjob%2F(\w+)', href)
            if match:
                job_id = match.group(1)
                job_url = f'https://builtin.com/job/{job_id}'
        # 3. Fallback: if the decoded href itself is a builtin.com/job/ link
        if not job_url and 'builtin.com/job/' in decoded_href:
            job_url = decoded_href
        # Only proceed if we found a job_url
        if job_url:
            # Extract inner divs for company, title, location, salary
            divs = a.find_all('div', recursive=False)
            company = title = location = salary = None
            if len(divs) >= 2:
                company = divs[0].get_text(strip=True)
                title = divs[1].get_text(strip=True)
            # Find location and salary in subsequent divs (look for span text)
            for div in divs[2:]:
                spans = div.find_all('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if text and ('$' in text or 'salary' in text.lower()):
                        salary = text
                    elif text and (',' in text or 'remote' in text.lower() or 'usa' in text.lower() or 'united states' in text.lower()):
                        location = text
            job = {
                'title': title,
                'company': company,
                'location': location,
                'salary_text': salary,
                'url': job_url,
                'source': 'builtin_email',
                'needs_enrichment': True,
                'raw_html': str(a),
            }
            jobs.append(job)
    return jobs

def color_log(msg, level='info'):
    colors = {
        'info': '\033[94m',      # Blue
        'warning': '\033[93m',   # Yellow
        'error': '\033[91m',     # Red
        'success': '\033[92m',   # Green
        'end': '\033[0m',        # Reset
    }
    color = colors.get(level, colors['info'])
    endc = colors['end']
    print(f"{color}{msg}{endc}", file=sys.stderr if level == 'error' else sys.stdout)

def fetch_and_store_jobs_from_gmail(
    parser_func,
    query,
    external_id_func=None,
    source_name=None,
    delete_after_fetch=False,
    db_path='../jobs.db',
):
    """
    Generic Gmail job extraction: fetches emails, parses jobs, saves to DB, logs results.
    parser_func: function(html) -> list of job dicts
    query: Gmail search query string
    external_id_func: function(url) -> external_id (optional)
    source_name: string for logging (optional)
    """
    color_log(f"[GMAIL EXTRACTION] Starting {source_name or 'job'} extraction from Gmail...", 'info')
    try:
        emails = fetch_job_alert_emails(query=query, delete_after_fetch=delete_after_fetch)
        color_log(f"[GMAIL EXTRACTION] Fetched {len(emails)} emails for query '{query}'", 'success')
        if emails:
            color_log(f"[GMAIL EXTRACTION] Sample email headers: {emails[0].get('headers', {})}", 'info')
            color_log(f"[GMAIL EXTRACTION] Sample email body (first 300 chars): {emails[0].get('body', '')[:300]}", 'info')
        all_jobs = []
        for email in emails:
            html = email.get('body', '')
            jobs = parser_func(html)
            color_log(f"[GMAIL EXTRACTION] Parsed {len(jobs)} jobs from email.", 'success' if jobs else 'warning')
            received_at = email.get('headers', {}).get('Date')
            for job in jobs:
                job['received_at'] = received_at
                if external_id_func and 'url' in job:
                    job['external_id'] = external_id_func(job.get('url', ''))
            all_jobs.extend([j for j in jobs if 'title' in j and 'url' in j])
        if all_jobs:
            db_result = save_jobs_to_db(all_jobs, db_path=db_path)
            color_log(f"[DB SAVE SUMMARY] Inserted: {db_result['inserted']}, Skipped (duplicates): {db_result['skipped']}, Failed: {db_result['failed']}", 'success')
            color_log(f"Saved {db_result['inserted']} new {source_name or 'jobs'} to DB. {db_result['skipped']} duplicates were skipped.", 'success')
            return db_result
        else:
            color_log(f"[GMAIL EXTRACTION] No {source_name or 'jobs'} found in Gmail extraction.", 'warning')
            color_log(f"No {source_name or 'jobs'} found to save.", 'warning')
            return {"inserted": 0, "skipped": 0, "failed": 0}
    except Exception as e:
        color_log(f"[GMAIL EXTRACTION] {source_name or 'Job'} extraction failed: {e}", 'error')
        return {"inserted": 0, "skipped": 0, "failed": 1, "error": str(e)}

def extract_linkedin_jobs_from_gmail(delete_after_fetch=False, db_path='../jobs.db'):
    """
    Extract and store LinkedIn jobs from Gmail.
    Uses the 'hopper/linkedin' label to fetch all relevant emails, regardless of sender.
    """
    return fetch_and_store_jobs_from_gmail(
        parser_func=parse_linkedin_job_alert_email,
        query='label:hopper/linkedin',  # Fetch all emails with this label
        external_id_func=extract_linkedin_job_id,
        source_name='LinkedIn',
        delete_after_fetch=delete_after_fetch,
        db_path=db_path,
    )


def extract_builtin_jobs_from_gmail(delete_after_fetch=False, db_path='../jobs.db'):
    """
    Extract and store BuiltIn jobs from Gmail.
    Uses the 'Hopper/builtin' label to fetch all relevant emails, regardless of sender.
    """
    return fetch_and_store_jobs_from_gmail(
        parser_func=parse_builtin_job_alert_email,
        query='label:Hopper/builtin',  # Fetch all emails with this label
        external_id_func=lambda url: url,  # Use job URL for deduplication
        source_name='BuiltIn',
        delete_after_fetch=delete_after_fetch,
        db_path=db_path,
    )

