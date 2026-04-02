from app.services.scraper import extract_status_id, parse_count, validate_x_url


def test_validate_x_url() -> None:
    assert validate_x_url("https://x.com/openai/status/123456789")
    assert validate_x_url("https://twitter.com/openai/status/123456789")
    assert validate_x_url("https://x.com/SarvamForDevs/status/2039187590726000904?s=20")
    assert not validate_x_url("https://example.com/openai/status/123456789")


def test_extract_status_id() -> None:
    assert extract_status_id("https://x.com/openai/status/123456789") == "123456789"


def test_parse_count() -> None:
    assert parse_count("1.2K") == 1200
    assert parse_count("3M") == 3_000_000
    assert parse_count("64") == 64
