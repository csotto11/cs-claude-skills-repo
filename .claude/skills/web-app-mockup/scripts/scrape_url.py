#!/usr/bin/env python3
"""Fetch and extract readable text from a URL.

Usage: python3 scrape_url.py "<URL>"

Output: JSON to stdout with keys "url", "title", and "text".
"""

import json
import re
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse


# Try to use BeautifulSoup if available, fall back to stdlib
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

REMOVE_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "iframe"}


class _LimitedRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Limit redirect hops to 5 to prevent redirect loops."""
    max_redirections = 5


_OPENER = urllib.request.build_opener(_LimitedRedirectHandler)

_RESPONSE_SIZE_LIMIT = 10 * 1024 * 1024  # 10 MB


def fetch_url(url):
    """Fetch HTML content from a URL."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with _OPENER.open(req, timeout=15) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read(_RESPONSE_SIZE_LIMIT)
        return raw.decode(charset, errors="replace")


def extract_with_bs4(html):
    """Extract text using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    for tag in soup.find_all(list(REMOVE_TAGS)):
        tag.decompose()

    body = soup.body if soup.body else soup
    text = body.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return title, text


class SimpleHTMLExtractor(HTMLParser):
    """Fallback HTML text extractor using stdlib."""

    def __init__(self):
        super().__init__()
        self.title = ""
        self.text_parts = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag in REMOVE_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in REMOVE_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.text_parts.append(stripped)


def extract_with_stdlib(html):
    """Extract text using stdlib HTMLParser."""
    parser = SimpleHTMLExtractor()
    parser.feed(html)
    title = parser.title.strip()
    text = "\n".join(parser.text_parts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return title, text


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 scrape_url.py <URL>"}))
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL scheme and host to prevent SSRF / protocol smuggling
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        print(json.dumps({"error": "Only HTTP/HTTPS URLs are supported"}))
        sys.exit(1)

    # Block loopback and well-known internal addresses
    hostname = (parsed.hostname or "").lower()
    _BLOCKED_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0", "169.254.169.254"}
    if hostname in _BLOCKED_HOSTS or hostname.startswith("127."):
        print(json.dumps({"error": "URL hostname is not allowed"}))
        sys.exit(1)

    try:
        html = fetch_url(url)
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch URL: {str(e)}"}))
        sys.exit(1)

    if HAS_BS4:
        title, text = extract_with_bs4(html)
    else:
        title, text = extract_with_stdlib(html)

    # Truncate to keep context manageable (shorter than job postings — a brief is enough)
    if len(text) > 8000:
        truncated = text[:8000]
        # Try to cut at a sentence or paragraph boundary
        last_para = truncated.rfind("\n\n")
        last_sentence = truncated.rfind(". ")
        cut_point = max(last_para, last_sentence)
        if cut_point > 5000:
            text = truncated[: cut_point + 1] + "\n\n[... truncated for length]"
        else:
            text = truncated + "\n\n[... truncated for length]"

    result = {
        "url": url,
        "title": title,
        "text": text
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
