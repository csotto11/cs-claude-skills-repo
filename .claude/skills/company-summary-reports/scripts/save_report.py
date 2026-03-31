#!/usr/bin/env python3
"""Save a company summary report to the output directory.

Usage: echo "report content" | python3 save_report.py "<company_name>"

Reads report content from stdin.
Saves to output/<company>_company_summary_<YYYY-MM-DD>.md
Prints JSON {"file": "<abs_path>", "filename": "<name>"} to stdout on success.
Prints JSON {"error": "<message>"} to stdout on failure (exit code 1).
"""

import json
import re
import sys
from datetime import date
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def sanitize_filename(name: str) -> str:
    """Convert a company name to a safe, lowercase filename component."""
    # Strip path separators and null bytes first to prevent traversal
    name = name.replace("/", "").replace("\\", "").replace("\x00", "")
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s-]+", "_", name)
    if not name:
        name = "untitled"
    return name


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: echo 'content' | python3 save_report.py <company_name>"}))
        sys.exit(1)

    company = sys.argv[1]
    content = sys.stdin.read()

    if not content.strip():
        print(json.dumps({"error": "No content provided on stdin"}))
        sys.exit(1)

    safe_name = sanitize_filename(company)
    today = date.today().isoformat()
    filename = f"{safe_name}_company_summary_{today}.md"
    output_path = (OUTPUT_DIR / filename).resolve()

    # Guard against path traversal using parent-directory check (not string prefix)
    if output_path.parent != OUTPUT_DIR.resolve():
        print(json.dumps({"error": "Invalid filename — path traversal detected"}))
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Normalize excessive blank lines while preserving intentional formatting
    formatted = content.strip()
    formatted = re.sub(r"\n{3,}", "\n\n", formatted)
    formatted = formatted + "\n"

    try:
        output_path.write_text(formatted, encoding="utf-8")
    except OSError as e:
        print(json.dumps({"error": f"Failed to write file: {e}"}))
        sys.exit(1)

    print(json.dumps({"file": str(output_path), "filename": filename}))


if __name__ == "__main__":
    main()
