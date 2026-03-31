#!/usr/bin/env python3
"""
Send The Sotto Voce newsletter via Resend API.

Usage:
    python send_newsletter.py --subject "The Sotto Voce — Vol. 1 | ..." --html-file output.html
    python send_newsletter.py --subject "..." --html "<html>...</html>"

Environment:
    RESEND_API_KEY          — Required. Your Resend API key.
    NEWSLETTER_FROM         — Optional. Sender address (default: onboarding@resend.dev).
    NEWSLETTER_RECIPIENTS   — Optional. Comma-separated emails (default: christian.sottosanti@gmail.com).
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

EDITION_TRACKER = Path(__file__).parent / "edition_tracker.json"

DEFAULT_FROM = "The Sotto Voce <onboarding@resend.dev>"
DEFAULT_RECIPIENTS = ["christian.sottosanti@gmail.com"]


def load_edition_tracker():
    if EDITION_TRACKER.exists():
        with open(EDITION_TRACKER) as f:
            return json.load(f)
    return {"edition": 0, "history": []}


def save_edition_tracker(data):
    with open(EDITION_TRACKER, "w") as f:
        json.dump(data, f, indent=2)


def get_next_edition():
    tracker = load_edition_tracker()
    tracker["edition"] += 1
    return tracker


def record_send(tracker, subject, recipients):
    tracker["history"].append({
        "edition": tracker["edition"],
        "subject": subject,
        "recipients": recipients,
        "sent_at": datetime.now(timezone.utc).isoformat(),
    })
    # Keep only last 52 entries (one year of weeklies)
    tracker["history"] = tracker["history"][-52:]
    save_edition_tracker(tracker)


def send_email(subject, html_content, from_addr=None, recipients=None):
    """Send email via Resend API."""
    try:
        import requests
    except ImportError:
        print("ERROR: 'requests' package not installed. Run: pip install requests")
        sys.exit(1)

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("ERROR: RESEND_API_KEY environment variable is not set.")
        print("Sign up at https://resend.com and set your API key.")
        sys.exit(1)

    from_addr = from_addr or os.environ.get("NEWSLETTER_FROM", DEFAULT_FROM)

    if recipients is None:
        env_recipients = os.environ.get("NEWSLETTER_RECIPIENTS")
        if env_recipients:
            recipients = [r.strip() for r in env_recipients.split(",")]
        else:
            recipients = DEFAULT_RECIPIENTS

    payload = {
        "from": from_addr,
        "to": recipients,
        "subject": subject,
        "html": html_content,
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    if response.status_code == 200:
        result = response.json()
        print(f"Email sent successfully! ID: {result.get('id', 'unknown')}")
        return True
    else:
        print(f"ERROR: Failed to send email. Status: {response.status_code}")
        print(f"Response: {response.text}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Send The Sotto Voce newsletter")
    parser.add_argument("--subject", required=True, help="Email subject line")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--html-file", help="Path to HTML file to send")
    group.add_argument("--html", help="Raw HTML string to send")
    parser.add_argument("--recipients", help="Comma-separated recipient emails")
    parser.add_argument("--from-addr", help="Sender address")
    parser.add_argument("--dry-run", action="store_true", help="Print instead of sending")

    args = parser.parse_args()

    # Load HTML content
    if args.html_file:
        html_path = Path(args.html_file)
        if not html_path.exists():
            print(f"ERROR: HTML file not found: {args.html_file}")
            sys.exit(1)
        html_content = html_path.read_text()
    else:
        html_content = args.html

    recipients = None
    if args.recipients:
        recipients = [r.strip() for r in args.recipients.split(",")]

    # Update edition tracker
    tracker = get_next_edition()
    edition_num = tracker["edition"]

    if args.dry_run:
        print(f"=== DRY RUN — Edition {edition_num} ===")
        print(f"Subject: {args.subject}")
        print(f"Recipients: {recipients or DEFAULT_RECIPIENTS}")
        print(f"HTML length: {len(html_content)} chars")
        print("Email NOT sent.")
        return

    # Send
    final_recipients = recipients or DEFAULT_RECIPIENTS
    success = send_email(
        subject=args.subject,
        html_content=html_content,
        from_addr=args.from_addr,
        recipients=final_recipients,
    )

    if success:
        record_send(tracker, args.subject, final_recipients)
        print(f"Edition {edition_num} recorded.")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
