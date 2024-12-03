"""Tests for the transform script."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
from transform import (
    convert_from_unix_to_datetime,
    convert_date_format,
    convert_to_full_url,
    validate_album_and_track,
    get_sale_information,
    get_genres_from_url,
    get_release_date_from_url,
    create_sales_dataframe
)

def test_convert_unix_to_datetime():
    assert convert_from_unix_to_datetime("1633036800") == "01-10-2021"
    assert convert_from_unix_to_datetime("invalid") == "None"

def test_convert_date_format():
    assert convert_date_format("1 October 2021") == "01-10-2021"
    assert convert_date_format("invalid date") == "None"

def test_convert_to_full_url():
    assert convert_to_full_url("http://example.com") == "http://example.com"
    assert convert_to_full_url("//example.com") == "https://example.com"

def test_validate_album_and_track():
    assert validate_album_and_track("a") is True
    assert validate_album_and_track("t") is True
    assert validate_album_and_track("x") is False

@patch("script_name.requests.get")
def test_get_genres_from_url(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '<a class="tag">Rock</a><a class="tag">Pop</a>'
    mock_get.return_value = mock_response

    assert set(get_genres_from_url("//example.com")) == {"Rock", "Pop"}
    mock_get.side_effect = Exception("Network Error")
    assert get_genres_from_url("//example.com") == []

@patch("script_name.requests.get")
def test_get_release_date_from_url(mock_get):
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
    mock_sales_info = [
        {
            "item_type": "a",
            "item_description": "Sample Album",
            "album_title": "Mock Album",
            "artist_name": "Mock Artist",
            "country": "US",
            "amount_paid_usd": 10.0,
            "genres": ["Rock", "Pop"],
            "release_date": "01-10-2021",
            "sale_date": "2021-10-01"
        }
    ]
    df = create_sales_dataframe(mock_sales_info)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "sale_year" in df.columns
    assert df.iloc[0]["sale_year"] == 2021