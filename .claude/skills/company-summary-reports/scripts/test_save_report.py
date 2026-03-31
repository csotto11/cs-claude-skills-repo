"""Tests for save_report.py

Each test invokes the script as a subprocess so that sys.argv and sys.stdin
can be controlled without monkeypatching module-level globals.

OUTPUT_DIR is temporarily redirected by overriding the constant inside the
subprocess via a small wrapper script.  This keeps tests hermetic — no files
land in the real output/ directory.

Note on the null-byte test: POSIX forbids null bytes in execve argument
vectors, so the OS itself raises ValueError before the subprocess even starts.
The null-byte strip in sanitize_filename is therefore tested as a direct unit
test by importing the function, which is the correct level of abstraction for
that particular behaviour.
"""

import json
import os
import re
import subprocess
import sys
import textwrap
from datetime import date
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Import sanitize_filename directly for unit tests that cannot use subprocess.
# save_report only calls main() under `if __name__ == "__main__"`, so importing
# it here is safe and has no side effects.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from save_report import sanitize_filename  # noqa: E402

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SCRIPT = Path(__file__).resolve().parent / "save_report.py"


def _run(
    company_name: str | None,
    stdin_content: str,
    tmp_output: Path,
) -> subprocess.CompletedProcess:
    """Run save_report.py in a subprocess with an overridden OUTPUT_DIR.

    The override is achieved by importing save_report inside the subprocess and
    patching OUTPUT_DIR before calling main().  This avoids touching production
    code while keeping each test fully isolated.
    """
    wrapper = textwrap.dedent(f"""\
        import sys, pathlib

        import save_report as _sr
        _sr.OUTPUT_DIR = pathlib.Path({str(tmp_output)!r})

        _sr.main()
    """)

    args = [sys.executable, "-c", wrapper]
    if company_name is not None:
        args.append(company_name)

    env = {**os.environ, "PYTHONPATH": str(SCRIPT.parent)}

    return subprocess.run(
        args,
        input=stdin_content,
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestHappyPath:
    """Valid company name and content — file is written, correct JSON returned."""

    def test_file_is_written(self, tmp_path):
        result = _run("Acme Corp", "# Report\n\nContent here.", tmp_path)
        assert result.returncode == 0, f"stderr: {result.stderr}"

        today = date.today().isoformat()
        expected_filename = f"acme_corp_company_summary_{today}.md"
        assert (tmp_path / expected_filename).exists()

    def test_stdout_is_valid_json(self, tmp_path):
        result = _run("Acme Corp", "# Report\n\nContent here.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "file" in data
        assert "filename" in data
        assert "error" not in data

    def test_filename_format(self, tmp_path):
        result = _run("Google LLC", "Some content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        today = date.today().isoformat()
        assert data["filename"] == f"google_llc_company_summary_{today}.md"

    def test_file_path_in_json_is_absolute(self, tmp_path):
        result = _run("Acme Corp", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert Path(data["file"]).is_absolute()

    def test_file_path_matches_filename(self, tmp_path):
        result = _run("Acme Corp", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["file"].endswith(data["filename"])

    def test_file_content_written_correctly(self, tmp_path):
        content = "# Report\n\nParagraph one.\n\nParagraph two."
        result = _run("Acme Corp", content, tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        written = Path(data["file"]).read_text(encoding="utf-8")
        assert "Paragraph one." in written
        assert "Paragraph two." in written

    def test_excessive_blank_lines_normalized(self, tmp_path):
        content = "Line one.\n\n\n\nLine two."
        result = _run("Acme Corp", content, tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        written = Path(data["file"]).read_text(encoding="utf-8")
        # Three or more consecutive newlines must be collapsed to two.
        assert "\n\n\n" not in written

    def test_output_ends_with_newline(self, tmp_path):
        result = _run("Acme Corp", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        written = Path(data["file"]).read_text(encoding="utf-8")
        assert written.endswith("\n")


class TestEmptyStdin:
    """Empty or whitespace-only stdin must return an error and exit 1."""

    def test_empty_string_returns_error_json(self, tmp_path):
        result = _run("Acme Corp", "", tmp_path)
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "error" in data

    def test_whitespace_only_returns_error_json(self, tmp_path):
        result = _run("Acme Corp", "   \n\t\n  ", tmp_path)
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "error" in data

    def test_no_file_written_on_empty_stdin(self, tmp_path):
        _run("Acme Corp", "", tmp_path)
        assert list(tmp_path.iterdir()) == []


class TestMissingArgv:
    """Missing company-name argument must return an error and exit 1."""

    def test_missing_arg_returns_error_json(self, tmp_path):
        # Pass None so _run omits the company name argument entirely.
        result = _run(None, "Some content.", tmp_path)
        assert result.returncode == 1
        data = json.loads(result.stdout)
        assert "error" in data

    def test_missing_arg_no_file_written(self, tmp_path):
        _run(None, "Some content.", tmp_path)
        assert list(tmp_path.iterdir()) == []


class TestSpecialCharactersInCompanyName:
    """Special characters in the company name must be sanitized in the filename."""

    def test_exclamation_removed(self, tmp_path):
        result = _run("Acme Corp!", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "!" not in data["filename"]

    def test_spaces_become_underscores(self, tmp_path):
        result = _run("Open AI", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["filename"].startswith("open_ai_")

    def test_mixed_special_chars(self, tmp_path):
        result = _run("Foo & Bar, Inc.", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # Only lowercase letters, digits, and underscores should appear in the
        # company-name portion of the filename.
        name_part = data["filename"].split("_company_summary_")[0]
        assert re.fullmatch(r"[a-z0-9_]+", name_part), (
            f"Unexpected characters in filename segment: {name_part!r}"
        )

    def test_filename_is_lowercase(self, tmp_path):
        result = _run("Google LLC", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        name_part = data["filename"].split("_company_summary_")[0]
        assert name_part == name_part.lower()

    def test_null_byte_stripped_from_name(self):
        """Null bytes cannot be passed via subprocess argv (POSIX constraint),
        so this is tested as a direct unit test of sanitize_filename."""
        result = sanitize_filename("Acme\x00Corp")
        assert "\x00" not in result
        # After stripping the null byte 'AcmeCorp' → 'acmecorp'
        assert result == "acmecorp"


class TestPathTraversal:
    """Company names designed to escape the output directory must be handled safely.

    sanitize_filename strips '/' and '\\' before building the filename, so
    '../evil' becomes 'evil'.  The resolved path therefore stays inside
    OUTPUT_DIR and the script succeeds (returns exit 0 with a valid file).
    These tests verify:
      1. No file is written outside the designated output directory.
      2. The sanitized filename is used, not the raw traversal string.
    """

    def test_dotdot_slash_does_not_escape_output_dir(self, tmp_path):
        result = _run("../evil", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        written_path = Path(data["file"])
        assert tmp_path in written_path.parents, (
            f"File {written_path} escaped the output directory {tmp_path}"
        )

    def test_dotdot_slash_sanitized_to_safe_name(self, tmp_path):
        result = _run("../evil", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        # '/' is stripped so '../evil' → sanitized to 'evil'
        today = date.today().isoformat()
        assert data["filename"] == f"evil_company_summary_{today}.md"

    def test_deep_traversal_stays_inside_output_dir(self, tmp_path):
        result = _run("../../etc/passwd", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        written_path = Path(data["file"])
        assert tmp_path in written_path.parents, (
            f"File {written_path} escaped the output directory {tmp_path}"
        )

    def test_backslash_traversal_stays_inside_output_dir(self, tmp_path):
        result = _run("..\\evil", "Content.", tmp_path)
        assert result.returncode == 0
        data = json.loads(result.stdout)
        written_path = Path(data["file"])
        assert tmp_path in written_path.parents
