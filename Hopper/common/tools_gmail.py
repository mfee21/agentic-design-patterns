"""
tools_gmail.py: Gmail integration for Hopper job aggregation system.
- Authenticates with Gmail using OAuth2 credentials.
- Fetches job alert emails (customizable by label, sender, or subject).
- Returns parsed email data for further processing.
- Contains only Gmail API and generic helpers (no job-source-specific parsing or orchestration).
"""
import os
import pickle
from typing import List, Dict, Any
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
import base64
import quopri
import logging

# If modifying these SCOPES, delete the token.pickle file.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), '../credentials.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), '../token.pickle')

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service

def decode_email_body(body: str) -> str:
    """
    Decodes a base64 or quoted-printable encoded email body.
    """
    try:
        # Try base64 decode
        return base64.urlsafe_b64decode(body + '===').decode('utf-8', errors='replace')
    except Exception:
        try:
            # Try quoted-printable decode
            return quopri.decodestring(body).decode('utf-8', errors='replace')
        except Exception:
            return body

def fetch_job_alert_emails(query: str = 'subject:(job alert)', delete_after_fetch: bool = False) -> List[Dict[str, Any]]:
    """
    Fetches emails matching the query from Gmail.
    Always prefers the HTML part if available.
    Optionally deletes emails after fetching.
    Args:
        query: Gmail search query string (e.g., 'from:jobs-noreply@linkedin.com')
        delete_after_fetch: If True, delete emails after fetching
    Returns:
        List of dicts with email metadata and raw content.
    """
    service = get_gmail_service()
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=20
    ).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get('payload', {})
        headers = {h['name']: h['value'] for h in payload.get('headers', [])}
        parts = payload.get('parts', [])
        body = ''
        # Prefer HTML part if available
        if parts:
            html_found = False
            for part in parts:
                if part.get('mimeType') == 'text/html':
                    body = decode_email_body(part.get('body', {}).get('data', ''))
                    html_found = True
                    break
            if not html_found:
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        body = decode_email_body(part.get('body', {}).get('data', ''))
                        break
        else:
            body = decode_email_body(payload.get('body', {}).get('data', ''))
        emails.append({
            'id': msg['id'],
            'threadId': msg.get('threadId'),
            'headers': headers,
            'body': body,
            'raw': msg_data
        })
        if delete_after_fetch:
            try:
                service.users().messages().delete(userId='me', id=msg['id']).execute()
            except Exception as e:
                print(f"Failed to delete email {msg['id']}: {e}")
    return emails
