#!/usr/bin/env python3
"""
Tests for the web-app-mockup scripts.
Uses only Python stdlib (unittest + unittest.mock).

Run with:
    python3 skills/web-app-mockup/tests/test_scripts.py
"""

import importlib
import io
import json
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the scripts directory importable regardless of cwd
# ---------------------------------------------------------------------------
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


# ===========================================================================
# install_deps.py tests
# ===========================================================================
class TestInstallDeps(unittest.TestCase):
    """Tests for install_deps.py module-level constants."""

    def setUp(self):
        # Import fresh so changes to sys.path above take effect
        import install_deps
        self.mod = install_deps

    def test_import_names_maps_beautifulsoup4_to_bs4(self):
        """IMPORT_NAMES must map 'beautifulsoup4' → 'bs4'."""
        self.assertIn("beautifulsoup4", self.mod.IMPORT_NAMES)
        self.assertEqual(self.mod.IMPORT_NAMES["beautifulsoup4"], "bs4")

    def test_required_packages_contains_beautifulsoup4(self):
        """REQUIRED_PACKAGES must list 'beautifulsoup4'."""
        self.assertIn("beautifulsoup4", self.mod.REQUIRED_PACKAGES)


# ===========================================================================
# scrape_url.py tests
# ===========================================================================
class TestScrapeUrl(unittest.TestCase):
    """Tests for scrape_url.py."""

    def setUp(self):
        import scrape_url
        self.mod = importlib.reload(scrape_url)  # reload to reset HAS_BS4 state

    # --- SSRF: file:// URL rejected by main() ---

    def test_main_rejects_file_url(self):
        """main() with a file:// URL must print JSON with 'error' key and exit 1."""
        with unittest.mock.patch.object(sys, "argv", ["scrape_url.py", "file:///etc/passwd"]):
            captured = io.StringIO()
            with unittest.mock.patch("sys.stdout", captured):
                with self.assertRaises(SystemExit) as ctx:
                    self.mod.main()
        self.assertEqual(ctx.exception.code, 1)
        output = captured.getvalue().strip()
        data = json.loads(output)
        self.assertIn("error", data)

    # --- SSRF: blank netloc (http:///etc/passwd) rejected by main() ---

    def test_main_rejects_blank_netloc(self):
        """main() with http:///etc/passwd (blank netloc) must exit 1 with error JSON."""
        with unittest.mock.patch.object(sys, "argv", ["scrape_url.py", "http:///etc/passwd"]):
            captured = io.StringIO()
            with unittest.mock.patch("sys.stdout", captured):
                with self.assertRaises(SystemExit) as ctx:
                    self.mod.main()
        self.assertEqual(ctx.exception.code, 1)
        output = captured.getvalue().strip()
        data = json.loads(output)
        self.assertIn("error", data)

    # --- extract_with_stdlib: basic happy path ---

    def test_extract_with_stdlib_returns_title_and_body(self):
        """extract_with_stdlib must return the page title and visible body text."""
        html = (
            "<html><head><title>Test Page</title></head>"
            "<body><p>Hello world</p></body></html>"
        )
        title, text = self.mod.extract_with_stdlib(html)
        self.assertEqual(title, "Test Page")
        self.assertIn("Hello world", text)

    def test_extract_with_stdlib_strips_script_tags(self):
        """extract_with_stdlib must not include content inside <script> tags."""
        html = (
            "<html><head><title>X</title></head>"
            "<body><p>Visible</p><script>hidden_code()</script></body></html>"
        )
        _, text = self.mod.extract_with_stdlib(html)
        self.assertIn("Visible", text)
        self.assertNotIn("hidden_code", text)

    def test_extract_with_stdlib_empty_html(self):
        """extract_with_stdlib on empty string returns empty title and text."""
        title, text = self.mod.extract_with_stdlib("")
        self.assertEqual(title, "")
        self.assertEqual(text, "")

    # --- Truncation: text longer than 8000 chars gets truncated ---

    def test_main_truncates_long_text(self):
        """main() must truncate extracted text longer than 8000 chars."""
        # Build HTML whose extracted body is over 8000 characters.
        # Use a paragraph boundary so the smart cut-point logic triggers.
        long_paragraph = ("A" * 80 + "\n\n") * 120   # ~9840 chars
        html_body = f"<p>{long_paragraph}</p>"
        html = (
            f"<html><head><title>Long</title></head>"
            f"<body>{html_body}</body></html>"
        )
        with unittest.mock.patch.object(sys, "argv", ["scrape_url.py", "http://example.com"]):
            with unittest.mock.patch.object(self.mod, "fetch_url", return_value=html):
                captured = io.StringIO()
                with unittest.mock.patch("sys.stdout", captured):
                    self.mod.main()
        data = json.loads(captured.getvalue().strip())
        self.assertIn("truncated for length", data["text"])
        # The raw text would be ~9840 chars; after truncation it must be shorter
        self.assertLess(len(data["text"]), 9000)


# ===========================================================================
# save_mockup.py tests
# ===========================================================================
class TestSaveMockup(unittest.TestCase):
    """Tests for save_mockup.py."""

    def setUp(self):
        import save_mockup
        self.mod = importlib.reload(save_mockup)

    # --- sanitize_filename ---

    def test_sanitize_acme_corp(self):
        """sanitize_filename('Acme Corp!') must return 'acme_corp'."""
        self.assertEqual(self.mod.sanitize_filename("Acme Corp!"), "acme_corp")

    def test_sanitize_empty_string(self):
        """sanitize_filename('') must return 'untitled'."""
        self.assertEqual(self.mod.sanitize_filename(""), "untitled")

    def test_sanitize_strips_path_separators(self):
        """sanitize_filename('../evil') must not contain '..' in the result."""
        result = self.mod.sanitize_filename("../evil")
        self.assertNotIn("..", result)
        # Also confirm no literal slash survives
        self.assertNotIn("/", result)
        self.assertNotIn("\\", result)

    def test_sanitize_null_bytes_stripped(self):
        """sanitize_filename must strip null bytes."""
        result = self.mod.sanitize_filename("a\x00b")
        self.assertNotIn("\x00", result)

    # --- Writing HTML to a temp output dir ---

    def test_main_writes_html_with_correct_naming_pattern(self):
        """main() must save a file named <slug>_mockup_<timestamp>.html."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # Patch OUTPUT_DIR inside the module so files land in tmpdir
            with unittest.mock.patch.object(self.mod, "OUTPUT_DIR", tmp_path):
                with unittest.mock.patch.object(
                    sys, "argv", ["save_mockup.py", "Acme Corp"]
                ):
                    fake_stdin = io.StringIO("<html><body>Hello</body></html>")
                    with unittest.mock.patch("sys.stdin", fake_stdin):
                        captured = io.StringIO()
                        with unittest.mock.patch("sys.stdout", captured):
                            self.mod.main()

            output = json.loads(captured.getvalue().strip())
            saved_file = Path(output["file"])
            self.assertTrue(saved_file.exists(), "Output file must exist on disk")
            # Name pattern: <slug>_mockup_<YYYYMMDD_HHMMSS>.html
            import re
            self.assertRegex(
                output["filename"],
                r"^[a-z0-9_]+_mockup_\d{8}_\d{6}\.html$",
            )

    # --- Path traversal guard ---

    def test_output_path_must_start_with_output_dir(self):
        """
        The resolved output path must always be inside OUTPUT_DIR.
        sanitize_filename already strips slashes, so no traversal is possible,
        but we verify the guard is effective: a crafted name cannot escape.
        """
        # After sanitization "../evil" becomes "evil" (dots stripped by regex).
        # Confirm the guard would still pass for a normal slug.
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with unittest.mock.patch.object(self.mod, "OUTPUT_DIR", tmp_path):
                with unittest.mock.patch.object(
                    sys, "argv", ["save_mockup.py", "../evil"]
                ):
                    fake_stdin = io.StringIO("<html><body>test</body></html>")
                    with unittest.mock.patch("sys.stdin", fake_stdin):
                        captured = io.StringIO()
                        with unittest.mock.patch("sys.stdout", captured):
                            self.mod.main()

            data = json.loads(captured.getvalue().strip())
            saved = Path(data["file"])
            # The saved path must be inside tmp_path (not escaped to parent)
            self.assertTrue(
                str(saved).startswith(str(tmp_path.resolve())),
                f"Output path {saved} is outside OUTPUT_DIR {tmp_path}",
            )

    def test_second_save_overwrites_not_appends(self):
        """Calling main() twice with the same slug must produce exactly one file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            for content in ("<html><body>First</body></html>", "<html><body>Second</body></html>"):
                with unittest.mock.patch.object(self.mod, "OUTPUT_DIR", tmp_path):
                    with unittest.mock.patch.object(
                        sys, "argv", ["save_mockup.py", "Acme Corp"]
                    ):
                        fake_stdin = io.StringIO(content)
                        with unittest.mock.patch("sys.stdin", fake_stdin):
                            captured = io.StringIO()
                            with unittest.mock.patch("sys.stdout", captured):
                                self.mod.main()
                # Reload so OUTPUT_DIR patch is fresh each iteration
                import save_mockup as _sm
                self.mod = importlib.reload(_sm)  # reset OUTPUT_DIR patch for next iteration

            html_files = list(tmp_path.glob("acme_corp_mockup_*.html"))
            self.assertEqual(len(html_files), 1, "Expected exactly one file after two saves")
            self.assertIn("Second", html_files[0].read_text(encoding="utf-8"))


# ===========================================================================
# serve_mockup.py tests
# ===========================================================================
class TestServeMockup(unittest.TestCase):
    """Tests for serve_mockup.py."""

    def setUp(self):
        import serve_mockup
        self.mod = importlib.reload(serve_mockup)

    # --- No args → exit 1 ---

    def test_main_no_args_exits_1(self):
        """main() with no arguments must exit with code 1."""
        with unittest.mock.patch.object(sys, "argv", ["serve_mockup.py"]):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.main()
        self.assertEqual(ctx.exception.code, 1)

    # --- Nonexistent file → exit 1 ---

    def test_main_nonexistent_file_exits_1(self):
        """main() with a nonexistent file path must exit with code 1."""
        with unittest.mock.patch.object(
            sys, "argv", ["serve_mockup.py", "/tmp/this_file_does_not_exist_xyz.html"]
        ):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.main()
        self.assertEqual(ctx.exception.code, 1)

    # --- Port 0 → invalid, exit 1 ---

    def test_main_port_0_exits_1(self):
        """Port 0 is outside the valid range 1–65535; main() must exit 1."""
        with unittest.mock.patch.object(
            sys, "argv", ["serve_mockup.py", "/some/file.html", "0"]
        ):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.main()
        self.assertEqual(ctx.exception.code, 1)

    # --- Port 99999 → invalid, exit 1 ---

    def test_main_port_99999_exits_1(self):
        """Port 99999 is above 65535; main() must exit 1."""
        with unittest.mock.patch.object(
            sys, "argv", ["serve_mockup.py", "/some/file.html", "99999"]
        ):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.main()
        self.assertEqual(ctx.exception.code, 1)

    # --- Valid port but missing file still exits 1 ---

    def test_main_valid_port_missing_file_exits_1(self):
        """A valid port with a nonexistent file must still exit 1."""
        with unittest.mock.patch.object(
            sys, "argv", ["serve_mockup.py", "/tmp/no_such_file_abc.html", "8080"]
        ):
            with self.assertRaises(SystemExit) as ctx:
                self.mod.main()
        self.assertEqual(ctx.exception.code, 1)


# ===========================================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
