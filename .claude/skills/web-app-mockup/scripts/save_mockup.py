#!/usr/bin/env python3
"""Save an HTML mockup to the output directory.

Usage: echo "<html>...</html>" | python3 save_mockup.py "<company_name>"

Reads HTML content from stdin.
Upsert behaviour: overwrites the existing <slug>_mockup_*.html file if one
exists, otherwise creates a new one with a timestamp suffix (first run only).
Prints JSON with "file" (absolute path) and "filename" to stdout.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def sanitize_filename(name):
    """Convert a name to a safe filename slug."""
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
        print("Usage: echo '<html>...</html>' | python3 save_mockup.py <company_name>", file=sys.stderr)
        sys.exit(1)

    company = sys.argv[1]
    content = sys.stdin.read()

    if not content.strip():
        print("Error: No content provided on stdin", file=sys.stderr)
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = sanitize_filename(company)

    # Upsert: reuse the existing file if one already exists for this slug.
    existing = sorted(
        OUTPUT_DIR.glob(f"{safe_name}_mockup_*.html"),
        key=lambda p: p.stat().st_mtime,
    )
    if existing:
        output_path = existing[-1].resolve()
        filename = output_path.name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_mockup_{timestamp}.html"
        output_path = (OUTPUT_DIR / filename).resolve()

    # Guard against path traversal — output must be a direct child of OUTPUT_DIR
    if output_path.parent != OUTPUT_DIR.resolve():
        print("Error: Invalid filename detected", file=sys.stderr)
        sys.exit(1)

    output_path.write_text(content, encoding="utf-8")

    result = {
        "file": str(output_path),
        "filename": filename
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
