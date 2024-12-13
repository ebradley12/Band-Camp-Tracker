"""Tests for the transform script."""

from unittest.mock import patch, MagicMock
from datetime import datetime
import pytest
import pandas as pd
from transform import (
    convert_from_unix_to_datetime,
    convert_date_format,
    convert_to_full_url,
    validate_album_and_track,
    get_genres_from_url,
    get_release_date_from_url,
    create_sales_dataframe,
)


@pytest.mark.parametrize("unix_input,expected", [
    ("1633036800", "01-10-2021"),
    ("invalid", "None"),
])
def test_convert_unix_to_datetime(unix_input, expected):
    """Test for convert_from_unix_to_datetime function."""
    assert convert_from_unix_to_datetime(unix_input) == expected


@pytest.mark.parametrize("date_input,expected", [
    ("1 October 2021", "01-10-2021"),
    ("invalid date", "None"),
])
def test_convert_date_format(date_input, expected):
    """Test for convert_date_format function."""
    assert convert_date_format(date_input) == expected


@pytest.mark.parametrize("url_input,expected", [
    ("http://example.com", "http://example.com"),
    ("//example.com", "https://example.com"),
])
def test_convert_to_full_url(url_input, expected):
    """Test for convert_to_full_url function."""
    assert convert_to_full_url(url_input) == expected


@pytest.mark.parametrize("item_type,expected", [
    ("a", True),
    ("t", True),
    ("x", False),
])
def test_validate_album_and_track(item_type, expected):
    """Test for validate_album_and_track function."""
    assert validate_album_and_track(item_type) == expected


@patch("transform.requests.get")
def test_get_genres_from_url(mock_get):
    """Test for get_genres_from_url function."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<a class="tag">Rock</a><a class="tag">Pop</a>'
    mock_get.return_value = mock_response
    locations = ["us", "rockville"]
    result = get_genres_from_url("//example.com", locations)
    assert set(result) == {"Rock", "Pop"}
    mock_get.side_effect = Exception("Network Error")
    assert get_genres_from_url("//example.com", locations) == []


@patch("transform.requests.get")
def test_get_release_date_from_url(mock_get):
    """Test for get_release_date_from_url function."""
    # Successful response with date
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<meta name="description" content="released 1 October 2021">'
    mock_get.return_value = mock_response
    assert get_release_date_from_url("//example.com") == "01-10-2021"
    mock_response.text = '<meta name="description" content="No release date">'
    mock_get.return_value = mock_response
    assert get_release_date_from_url("//example.com") == ""
    mock_get.side_effect = Exception("Network Error")
    assert get_release_date_from_url("//example.com") == ""


def test_create_sales_dataframe():
    """Test for create_sales_dataframe function."""
    mock_sales_info = [
        {
            "release_type": "a",
            "release_description": "Sample Album",
            "album_title": "Mock Album",
            "artist_name": "Mock Artist",
            "country": "US",
            "amount_paid_usd": 10.0,
            "genres": ["Rock", "Pop"],
            "release_date": "01-10-2021",
            "sale_date": "2021-10-01",
        }
    ]
    df = create_sales_dataframe(mock_sales_info)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "item_type" in df.columns
    assert df.iloc[0]["item_type"] == "a"
