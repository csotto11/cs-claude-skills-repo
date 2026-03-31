#!/usr/bin/env python3
"""Save a cover letter to the output directory.

Usage: echo "cover letter content" | python3 save_cover_letter.py "<company_name>"

Reads cover letter content from stdin.
Saves to output/<company>_cover_letter_<YYYY-MM-DD>.md
Prints the absolute output file path to stdout.
"""

import re
import sys
from datetime import date
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def sanitize_filename(name):
    """Convert company name to a safe filename component."""
    # Strip path separators and null bytes first
    name = name.replace("/", "").replace("\\", "").replace("\x00", "")
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s-]", "", name)
    name = re.sub(r"[\s-]+", "_", name)
    if not name:
        name = "untitled"
    return name


def main():
    if len(sys.argv) < 2:
        print("Usage: echo 'content' | python3 save_cover_letter.py <company_name>", file=sys.stderr)
        sys.exit(1)

    company = sys.argv[1]
    content = sys.stdin.read()

    if not content.strip():
        print("Error: No content provided on stdin", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(company)
    today = date.today().isoformat()
    filename = f"{safe_name}_cover_letter_{today}.md"
    output_path = (OUTPUT_DIR / filename).resolve()

    # Guard against path traversal
    if not str(output_path).startswith(str(OUTPUT_DIR.resolve())):
        print("Error: Invalid filename detected", file=sys.stderr)
        sys.exit(1)

    # Normalize excessive blank lines without restructuring intentional formatting
    formatted = content.strip()
    formatted = re.sub(r"\n{3,}", "\n\n", formatted)
    formatted = formatted + "\n"

    output_path.write_text(formatted, encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
