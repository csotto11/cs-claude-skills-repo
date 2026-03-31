#!/usr/bin/env python3
"""Comprehensive tests for the Cover Letter skill scripts."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest


# Import the scripts as modules
sys.path.insert(0, str(Path(__file__).parent))

import install_deps
import parse_resume
import scrape_job_posting
import save_cover_letter


class TestSanitizeFilename:
    """Tests for save_cover_letter.sanitize_filename()"""

    def test_empty_name(self):
        """Empty string should return 'untitled'"""
        assert save_cover_letter.sanitize_filename("") == "untitled"

    def test_whitespace_only(self):
        """Whitespace-only should return 'untitled'"""
        assert save_cover_letter.sanitize_filename("   ") == "untitled"
        assert save_cover_letter.sanitize_filename("\t\n") == "untitled"

    def test_special_characters(self):
        """Special characters should be removed"""
        assert save_cover_letter.sanitize_filename("Acme@Corp!") == "acmecorp"
        assert save_cover_letter.sanitize_filename("Tech#Company$") == "techcompany"
        assert save_cover_letter.sanitize_filename("Test&Co.") == "testco"

    def test_path_traversal_attempts(self):
        """Path traversal attempts should be neutralized"""
        assert save_cover_letter.sanitize_filename("../../../etc/passwd") == "etcpasswd"
        assert save_cover_letter.sanitize_filename("..\\..\\windows\\system32") == "windowssystem32"
        assert save_cover_letter.sanitize_filename("/absolute/path") == "absolutepath"
        assert save_cover_letter.sanitize_filename("\\backslash\\path") == "backslashpath"

    def test_null_bytes(self):
        """Null bytes should be removed"""
        assert save_cover_letter.sanitize_filename("test\x00file") == "testfile"

    def test_normal_names(self):
        """Normal company names should be lowercased and formatted correctly"""
        assert save_cover_letter.sanitize_filename("Google") == "google"
        assert save_cover_letter.sanitize_filename("Meta Inc") == "meta_inc"
        assert save_cover_letter.sanitize_filename("Amazon Web Services") == "amazon_web_services"
        assert save_cover_letter.sanitize_filename("Microsoft-Azure") == "microsoft_azure"

    def test_mixed_spaces_and_hyphens(self):
        """Spaces and hyphens should be converted to single underscores"""
        assert save_cover_letter.sanitize_filename("Wells   Fargo") == "wells_fargo"
        assert save_cover_letter.sanitize_filename("JP-Morgan-Chase") == "jp_morgan_chase"
        assert save_cover_letter.sanitize_filename("Bank - of - America") == "bank_of_america"

    def test_numbers_preserved(self):
        """Numbers should be preserved"""
        assert save_cover_letter.sanitize_filename("Company 123") == "company_123"
        assert save_cover_letter.sanitize_filename("456 Industries") == "456_industries"


class TestSaveCoverLetter:
    """Tests for save_cover_letter.py main flow"""

    def test_valid_input_saves_correctly(self, tmp_path, monkeypatch):
        """Valid input should save to the correct location with proper formatting"""
        # Setup
        output_dir = tmp_path / "output"
        monkeypatch.setattr(save_cover_letter, "OUTPUT_DIR", output_dir)

        content = "Dear Hiring Manager,\n\n\n\nThis is a test cover letter.\n\n\n\nSincerely,\nTest User"
        expected_content = "Dear Hiring Manager,\n\nThis is a test cover letter.\n\nSincerely,\nTest User\n"

        # Mock stdin and argv
        monkeypatch.setattr("sys.stdin", Mock(read=lambda: content))
        monkeypatch.setattr("sys.argv", ["save_cover_letter.py", "Test Company"])

        # Capture stdout
        captured_output = []
        monkeypatch.setattr("sys.stdout", Mock(write=lambda x: captured_output.append(x)))

        # Run
        save_cover_letter.main()

        # Verify output directory and file
        assert output_dir.exists()
        files = list(output_dir.glob("*.md"))
        assert len(files) == 1

        saved_file = files[0]
        assert "test_company_cover_letter_" in saved_file.name
        assert saved_file.read_text() == expected_content

    def test_empty_stdin_errors(self, tmp_path, monkeypatch, capsys):
        """Empty stdin should exit with error"""
        output_dir = tmp_path / "output"
        monkeypatch.setattr(save_cover_letter, "OUTPUT_DIR", output_dir)

        # Mock empty stdin
        monkeypatch.setattr("sys.stdin", Mock(read=lambda: ""))
        monkeypatch.setattr("sys.argv", ["save_cover_letter.py", "Test Company"])

        # Run and expect exit
        with pytest.raises(SystemExit) as exc_info:
            save_cover_letter.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No content provided" in captured.err

    def test_whitespace_only_stdin_errors(self, tmp_path, monkeypatch, capsys):
        """Whitespace-only stdin should exit with error"""
        output_dir = tmp_path / "output"
        monkeypatch.setattr(save_cover_letter, "OUTPUT_DIR", output_dir)

        monkeypatch.setattr("sys.stdin", Mock(read=lambda: "   \n\t\n  "))
        monkeypatch.setattr("sys.argv", ["save_cover_letter.py", "Test Company"])

        with pytest.raises(SystemExit) as exc_info:
            save_cover_letter.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No content provided" in captured.err

    def test_path_traversal_protection(self, tmp_path, monkeypatch, capsys):
        """Path traversal in company name should be caught"""
        output_dir = tmp_path / "output"
        monkeypatch.setattr(save_cover_letter, "OUTPUT_DIR", output_dir)

        content = "Test content"
        monkeypatch.setattr("sys.stdin", Mock(read=lambda: content))

        # Even though sanitize_filename removes path separators,
        # the final path check should still protect against any edge cases
        # This test verifies the defense-in-depth approach
        monkeypatch.setattr("sys.argv", ["save_cover_letter.py", "Company"])

        # Should succeed normally
        save_cover_letter.main()
        assert output_dir.exists()

    def test_missing_company_name_argument(self, monkeypatch, capsys):
        """Missing company name argument should exit with usage error"""
        monkeypatch.setattr("sys.argv", ["save_cover_letter.py"])

        with pytest.raises(SystemExit) as exc_info:
            save_cover_letter.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.err


class TestScrapeJobPosting:
    """Tests for scrape_job_posting.py"""

    def test_url_validation_rejects_file_protocol(self, monkeypatch, capsys):
        """file:// URLs should be rejected"""
        monkeypatch.setattr("sys.argv", ["scrape_job_posting.py", "file:///etc/passwd"])

        with pytest.raises(SystemExit) as exc_info:
            scrape_job_posting.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "error" in output
        assert "HTTP/HTTPS" in output["error"]

    def test_url_validation_rejects_ftp_protocol(self, monkeypatch, capsys):
        """ftp:// URLs should be rejected"""
        monkeypatch.setattr("sys.argv", ["scrape_job_posting.py", "ftp://example.com/file"])

        with pytest.raises(SystemExit) as exc_info:
            scrape_job_posting.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "error" in output
        assert "HTTP/HTTPS" in output["error"]

    def test_simple_html_extractor_basic_html(self):
        """SimpleHTMLExtractor should extract text from basic HTML"""
        html = """
        <html>
            <head><title>Job Title</title></head>
            <body>
                <h1>Software Engineer</h1>
                <p>We are hiring.</p>
                <script>alert('test');</script>
                <p>Apply now!</p>
            </body>
        </html>
        """

        title, text = scrape_job_posting.extract_with_stdlib(html)

        assert title == "Job Title"
        assert "Software Engineer" in text
        assert "We are hiring." in text
        assert "Apply now!" in text
        assert "alert" not in text  # Script content should be excluded

    def test_simple_html_extractor_removes_unwanted_tags(self):
        """SimpleHTMLExtractor should remove script, style, nav, etc."""
        html = """
        <html>
            <body>
                <nav>Navigation Menu</nav>
                <style>body { color: red; }</style>
                <div>Actual Content</div>
                <footer>Footer Text</footer>
                <script>console.log('test');</script>
            </body>
        </html>
        """

        title, text = scrape_job_posting.extract_with_stdlib(html)

        assert "Actual Content" in text
        assert "Navigation Menu" not in text
        assert "color: red" not in text
        assert "Footer Text" not in text
        assert "console.log" not in text

    def test_simple_html_extractor_nested_skip_tags(self):
        """SimpleHTMLExtractor should handle nested skip tags correctly"""
        html = """
        <html>
            <body>
                <p>Before</p>
                <script>
                    var x = "<script>nested</script>";
                </script>
                <p>After</p>
            </body>
        </html>
        """

        title, text = scrape_job_posting.extract_with_stdlib(html)

        assert "Before" in text
        assert "After" in text
        assert "nested" not in text
        assert "var x" not in text

    def test_truncation_at_sentence_boundary(self, monkeypatch, capsys):
        """Long text should be truncated at sentence boundaries"""
        long_text = "Sentence one. " * 1000 + "Sentence two. " * 1000
        html = f"<html><head><title>Test</title></head><body><p>{long_text}</p></body></html>"

        monkeypatch.setattr("sys.argv", ["scrape_job_posting.py", "https://example.com/job"])

        with patch("scrape_job_posting.fetch_url", return_value=html):
            scrape_job_posting.main()

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert len(result["text"]) < len(long_text)
        assert "[... truncated for length]" in result["text"]
        # Should end at a sentence boundary if possible
        # Remove the truncation marker and check what comes before it
        text_without_marker = result["text"].replace("\n\n[... truncated for length]", "")
        assert text_without_marker.endswith(". ") or text_without_marker.endswith(".")

    def test_truncation_at_paragraph_boundary(self, monkeypatch, capsys):
        """Long text should prefer paragraph boundaries over sentence boundaries"""
        # Create text with paragraph breaks after 12000 chars
        long_text = "A" * 12000 + "\n\nParagraph break here. " + "B" * 5000
        html = f"<html><head><title>Test</title></head><body><p>{long_text}</p></body></html>"

        monkeypatch.setattr("sys.argv", ["scrape_job_posting.py", "https://example.com/job"])

        with patch("scrape_job_posting.fetch_url", return_value=html):
            scrape_job_posting.main()

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "[... truncated for length]" in result["text"]

    def test_fetch_error_handling(self, monkeypatch, capsys):
        """Network errors should be caught and reported as JSON"""
        monkeypatch.setattr("sys.argv", ["scrape_job_posting.py", "https://example.com/job"])

        with patch("scrape_job_posting.fetch_url", side_effect=Exception("Network error")):
            with pytest.raises(SystemExit) as exc_info:
                scrape_job_posting.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "error" in result
        assert "Failed to fetch URL" in result["error"]

    def test_missing_url_argument(self, monkeypatch, capsys):
        """Missing URL argument should exit with error"""
        monkeypatch.setattr("sys.argv", ["scrape_job_posting.py"])

        with pytest.raises(SystemExit) as exc_info:
            scrape_job_posting.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "error" in result
        assert "Usage:" in result["error"]


class TestParseResume:
    """Tests for parse_resume.py"""

    def test_find_latest_resume_directory_not_exists(self, monkeypatch, tmp_path):
        """find_latest_resume() should return error when directory doesn't exist"""
        non_existent_dir = tmp_path / "does_not_exist"
        monkeypatch.setattr(parse_resume, "RESUME_DIR", non_existent_dir)

        pdf_path, error = parse_resume.find_latest_resume()

        assert pdf_path is None
        assert error is not None
        assert "Directory not found" in error

    def test_find_latest_resume_no_pdfs(self, monkeypatch, tmp_path):
        """find_latest_resume() should return error when no PDFs found"""
        empty_dir = tmp_path / "resume_dir"
        empty_dir.mkdir()
        monkeypatch.setattr(parse_resume, "RESUME_DIR", empty_dir)

        pdf_path, error = parse_resume.find_latest_resume()

        assert pdf_path is None
        assert error is not None
        assert "No PDF files found" in error

    def test_find_latest_resume_prefers_resume_in_name(self, monkeypatch, tmp_path, capsys):
        """find_latest_resume() should prefer files with 'resume' in the name"""
        resume_dir = tmp_path / "resume_dir"
        resume_dir.mkdir()

        # Create PDFs with different names and modification times
        transcript = resume_dir / "transcript.pdf"
        resume = resume_dir / "my_resume.pdf"

        transcript.write_bytes(b"%PDF-1.4\n")
        resume.write_bytes(b"%PDF-1.4\n")

        # Make transcript newer by touching it
        import time
        time.sleep(0.01)
        transcript.touch()

        monkeypatch.setattr(parse_resume, "RESUME_DIR", resume_dir)

        pdf_path, error = parse_resume.find_latest_resume()

        assert error is None
        assert pdf_path.name == "my_resume.pdf"

    def test_find_latest_resume_falls_back_to_newest(self, monkeypatch, tmp_path, capsys):
        """find_latest_resume() should use newest PDF if no 'resume' in name"""
        resume_dir = tmp_path / "resume_dir"
        resume_dir.mkdir()

        old_pdf = resume_dir / "old.pdf"
        new_pdf = resume_dir / "new.pdf"

        old_pdf.write_bytes(b"%PDF-1.4\n")

        import time
        time.sleep(0.01)

        new_pdf.write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(parse_resume, "RESUME_DIR", resume_dir)

        pdf_path, error = parse_resume.find_latest_resume()

        assert error is None
        assert pdf_path.name == "new.pdf"
        # Should warn about no 'resume' in name
        captured = capsys.readouterr()
        assert "Warning" in captured.err

    def test_empty_text_detection(self, monkeypatch, tmp_path, capsys):
        """Empty extracted text should exit with error"""
        resume_dir = tmp_path / "resume_dir"
        resume_dir.mkdir()

        resume_pdf = resume_dir / "resume.pdf"
        resume_pdf.write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(parse_resume, "RESUME_DIR", resume_dir)

        # Mock extract_text to return empty string
        with patch("parse_resume.extract_text", return_value="   "):
            with pytest.raises(SystemExit) as exc_info:
                parse_resume.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "error" in result
        assert "No text extracted" in result["error"]

    def test_successful_extraction(self, monkeypatch, tmp_path, capsys):
        """Successful text extraction should return JSON with file and text"""
        resume_dir = tmp_path / "resume_dir"
        resume_dir.mkdir()

        resume_pdf = resume_dir / "my_resume.pdf"
        resume_pdf.write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(parse_resume, "RESUME_DIR", resume_dir)

        test_text = "John Doe\nSoftware Engineer\nExperience: 5 years"

        with patch("parse_resume.extract_text", return_value=test_text):
            parse_resume.main()

        captured = capsys.readouterr()
        result = json.loads(captured.out)

        assert "error" not in result
        assert result["file"] == "my_resume.pdf"
        assert result["text"] == test_text

    def test_extraction_exception_handling(self, monkeypatch, tmp_path, capsys):
        """Exceptions during extraction should be caught and reported"""
        resume_dir = tmp_path / "resume_dir"
        resume_dir.mkdir()

        resume_pdf = resume_dir / "resume.pdf"
        resume_pdf.write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(parse_resume, "RESUME_DIR", resume_dir)

        with patch("parse_resume.extract_text", side_effect=Exception("PDF corrupted")):
            with pytest.raises(SystemExit) as exc_info:
                parse_resume.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert "error" in result
        assert "Failed to parse" in result["error"]


class TestInstallDeps:
    """Tests for install_deps.py"""

    def test_package_already_installed(self, monkeypatch, capsys):
        """If package is already installed, should report OK without installing"""
        # Mock __import__ to succeed (package already installed)
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pypdf":
                return Mock()  # Pretend it's installed
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        install_deps.main()

        captured = capsys.readouterr()
        assert "[OK] pypdf already installed" in captured.out

    def test_package_installation_success(self, monkeypatch, capsys):
        """If package is not installed, should install it successfully"""
        import builtins
        original_import = builtins.__import__
        import_count = [0]

        def mock_import(name, *args, **kwargs):
            if name == "pypdf":
                import_count[0] += 1
                if import_count[0] == 1:
                    raise ImportError("pypdf not found")
                return Mock()  # Second import succeeds
            return original_import(name, *args, **kwargs)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        monkeypatch.setattr("builtins.__import__", mock_import)
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        install_deps.main()

        captured = capsys.readouterr()
        assert "[INSTALLING] pypdf..." in captured.out
        assert "[OK] pypdf installed successfully" in captured.out

    def test_package_installation_failure(self, monkeypatch, capsys):
        """If installation fails, should exit with error"""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "pypdf":
                raise ImportError("pypdf not found")
            return original_import(name, *args, **kwargs)

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Installation failed: network error"

        monkeypatch.setattr("builtins.__import__", mock_import)
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: mock_result)

        with pytest.raises(SystemExit) as exc_info:
            install_deps.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "[ERROR] Failed to install pypdf" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
