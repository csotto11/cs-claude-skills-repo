#!/usr/bin/env python3
"""One-time dependency installer for the cover letter skill."""

import subprocess
import sys


REQUIRED_PACKAGES = ["pypdf"]


def main():
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
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
