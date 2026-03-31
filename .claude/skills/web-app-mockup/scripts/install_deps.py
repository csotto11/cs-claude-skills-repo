#!/usr/bin/env python3
"""One-time dependency installer for the web-app-mockup skill."""

import subprocess
import sys


REQUIRED_PACKAGES = ["beautifulsoup4"]

# Map install name → import name when they differ
IMPORT_NAMES = {"beautifulsoup4": "bs4"}


def main():
    for package in REQUIRED_PACKAGES:
        import_name = IMPORT_NAMES.get(package, package)
        try:
            __import__(import_name)
            print(f"[OK] {package} already installed")
        except ImportError:
            print(f"[INSTALLING] {package}...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"[OK] {package} installed successfully")
            else:
                print(f"[ERROR] Failed to install {package}: {result.stderr}", file=sys.stderr)
                sys.exit(1)

    print("\nAll dependencies ready.")


if __name__ == "__main__":
    main()
