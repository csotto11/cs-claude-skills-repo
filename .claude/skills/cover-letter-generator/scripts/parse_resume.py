#!/usr/bin/env python3
"""Extract text from the most recently modified resume PDF.

Scans ~/Desktop/Resume and Transcript/ for PDF files,
picks the most recently modified one, and extracts its text.

Output: JSON to stdout with keys "file" and "text".
"""

import json
import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print(json.dumps({"error": "pypdf not installed. Run: python3 scripts/install_deps.py"}))
    sys.exit(1)


RESUME_DIR = Path.home() / "Desktop" / "Resume and Transcript"


def find_latest_resume():
    """Find the most recently modified PDF in the resume directory."""
    if not RESUME_DIR.exists():
        return None, f"Directory not found: {RESUME_DIR}"

    pdfs = sorted(RESUME_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)

    # Filter out non-resume files (transcripts, score reports, etc.)
    resume_pdfs = [p for p in pdfs if "resume" in p.name.lower()]

    if resume_pdfs:
        return resume_pdfs[0], None
    elif pdfs:
        import sys as _sys
        print(
            f"Warning: No file with 'resume' in name found. Using most recent PDF: {pdfs[0].name}",
            file=_sys.stderr,
        )
        return pdfs[0], None
    else:
        return None, f"No PDF files found in {RESUME_DIR}"


def extract_text(pdf_path):
    """Extract all text from a PDF using pypdf."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)
    return "\n\n".join(pages_text)


def main():
    pdf_path, error = find_latest_resume()

    if error:
        print(json.dumps({"error": error}))
        sys.exit(1)

    try:
        text = extract_text(pdf_path)
        if not text.strip():
            print(json.dumps({
                "error": f"No text extracted from {pdf_path.name}. File may be image-only or corrupted. Paste resume text directly."
            }))
            sys.exit(1)
        result = {
            "file": pdf_path.name,
            "text": text
        }
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse {pdf_path.name}: {str(e)}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
