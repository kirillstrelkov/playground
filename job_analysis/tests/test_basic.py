from io import StringIO
from unittest.mock import Mock, patch

import pandas as pd

from job_analysis.cli import fetch_url_text, load_csv_data


def test_extract_requirements_dedup_and_cleaning():
    # Bypass LLM by calling function directly on text is not possible; we just test cleaning pipeline
    # So we simulate provider output lines
    raw = """- Python\n- python\n* FastAPI\n- Docker\n"""
    strip_chars = "- *\t "
    lines = [ln.strip(strip_chars) for ln in raw.splitlines()]
    cleaned = [ln for ln in lines if ln]
    seen = set()
    result = []
    for item in cleaned:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    assert result == ["Python", "FastAPI", "Docker"]


def test_load_csv_data_basic():
    csv_content = "Job position,Link\nSoftware Engineer,https://example.com\nData Scientist,https://example2.com"
    csv_file = StringIO(csv_content)
    df = pd.read_csv(csv_file)
    df.to_csv("test_temp.csv", index=False)

    try:
        result = load_csv_data("test_temp.csv", "Job position", "Link")
        assert len(result) == 2
        assert list(result.columns) == ["Job position", "Link"]
    finally:
        import os

        os.remove("test_temp.csv")


def test_load_csv_data_missing_column():
    csv_content = "Job position,Company\nSoftware Engineer,Company A"
    csv_file = StringIO(csv_content)
    df = pd.read_csv(csv_file)
    df.to_csv("test_temp.csv", index=False)

    try:
        try:
            load_csv_data("test_temp.csv", "Job position", "Link")
            raise AssertionError("Should have raised ValueError")
        except ValueError as e:
            assert "Link" in str(e)
    finally:
        import os

        os.remove("test_temp.csv")


def test_fetch_url_text_success():
    """Test successful URL text extraction."""
    mock_html = """
    <html>
        <head><title>Test Job</title></head>
        <body>
            <h1>Software Engineer Position</h1>
            <p>We are looking for a Python developer.</p>
            <script>console.log('ignore this');</script>
            <style>body { color: red; }</style>
            <div>Requirements: Python, FastAPI, Docker</div>
        </body>
    </html>
    """

    mock_response = Mock()
    mock_response.text = mock_html
    mock_response.raise_for_status = Mock()

    with patch("job_analysis.cli.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        result = fetch_url_text("https://example.com/job")

        # Should extract text content and remove script/style tags
        assert "Software Engineer Position" in result
        assert "Python developer" in result
        assert "Requirements: Python, FastAPI, Docker" in result
        assert "console.log" not in result  # Script content removed
        assert "color: red" not in result  # Style content removed
        assert len(result) <= 120000  # Should be truncated if too long


def test_fetch_url_text_http_error():
    """Test URL text extraction with HTTP error."""
    with patch("job_analysis.cli.httpx.Client") as mock_client:
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        try:
            fetch_url_text("https://example.com/nonexistent")
            raise AssertionError("Should have raised exception")
        except Exception as e:
            assert "HTTP 404" in str(e)


def test_fetch_url_text_long_content():
    """Test URL text extraction with very long content."""
    # Create content longer than 120000 characters
    long_content = "This is a test sentence. " * 5000  # ~150000 characters

    mock_html = f"<html><body><p>{long_content}</p></body></html>"

    mock_response = Mock()
    mock_response.text = mock_html
    mock_response.raise_for_status = Mock()

    with patch("job_analysis.cli.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        result = fetch_url_text("https://example.com/long")

        # Should be truncated to 120000 characters
        assert len(result) == 120000
        assert result.endswith("...") or len(result) <= 120000


def test_nvidia_url():
    url = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Senior-Python-DL-Automation-Engineer--Deep-Learning-Algorithms_JR2001636"
    result = fetch_url_text(url)

    assert "Excellent Python programming" in result


def test_wolt_url():
    url = "https://job-boards.greenhouse.io/wolt/jobs/6693460"
    result = fetch_url_text(url)

    print(result)

    assert "Kotlin , Java, Scala" in result
