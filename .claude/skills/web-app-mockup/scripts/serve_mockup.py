#!/usr/bin/env python3
"""Serve a single HTML mockup file on a local HTTP server.

Usage: python3 serve_mockup.py <path/to/file.html> [port]

Serves from the file's directory so relative assets resolve correctly.
Opens the file in the default browser automatically.
Press Ctrl+C to stop.
"""

import http.server
import os
import sys
import webbrowser
from pathlib import Path


DEFAULT_PORT = 8080


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with request logging suppressed."""

    def log_message(self, format, *args):
        pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 serve_mockup.py <path/to/file.html> [port]", file=sys.stderr)
        sys.exit(1)

    file_path = Path(sys.argv[1]).resolve()
    try:
        port = int(sys.argv[2]) if len(sys.argv) >= 3 else DEFAULT_PORT
    except ValueError:
        print(f"Error: Port must be an integer, got {sys.argv[2]!r}", file=sys.stderr)
        sys.exit(1)

    if not (1 <= port <= 65535):
        print(f"Error: Port must be between 1 and 65535, got {port}", file=sys.stderr)
        sys.exit(1)

    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Serve from the file's directory so relative paths work
    os.chdir(file_path.parent)

    url = f"http://localhost:{port}/{file_path.name}"

    try:
        server = http.server.HTTPServer(("127.0.0.1", port), _QuietHandler)
    except OSError as e:
        print(f"Error: Could not bind to port {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Serving mockup at: {url}")
    print("Press Ctrl+C to stop.\n")

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
