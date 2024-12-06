"""test_etl.py: Unit tests for the ETL process.

This script tests the entire ETL process:
- Extraction of sales data from the API.
- Transformation of extracted data.
- Loading of transformed data into a database.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import requests
import os
import pandas as pd
import numpy as np
from extract import get_sales_information
from transform import (
    convert_from_unix_to_datetime,
    convert_date_format,
    convert_to_full_url,
    validate_album_and_track,
    get_genres_from_url,
    get_release_date_from_url,
    create_sales_dataframe,
    fill_out_album_and_track,
)
from load import (
    get_connection,
    get_cursor,
    insert_country,
    insert_artist,
    insert_genres,
    get_id_from_table,
    main_load,
)

class TestExtract:
    """Tests for the extract phase of the ETL process."""

    @patch("extract.requests.get")
    def test_extract_get_sales_information_success(self, mock_get):
        """Verify successful data extraction from the API."""
        mock_response = MagicMock(status_code=200, json=lambda: {"sales": "data"})
        mock_get.return_value = mock_response

        result = get_sales_information()
        assert result == {"sales": "data"}
        mock_get.assert_called_once_with(
            "https://bandcamp.com/api/salesfeed/1/get_initial", timeout=1000
        )

    @patch("extract.requests.get")
    def test_extract_get_sales_information_failure(self, mock_get):
        """Verify API failure handling."""
        mock_response = MagicMock(status_code=404)
        mock_get.return_value = mock_response

        result = get_sales_information()
        assert result == {}
        mock_get.assert_called_once()
    
    @patch("extract.requests.get")
    def test_extract_get_sales_information_invalid_json(self, mock_get):
        """Verify handling of an invalid JSON response."""
        mock_response = MagicMock(status_code=200, json=lambda: None)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        result = get_sales_information()
        assert result == None
        mock_get.assert_called_once_with(
            "https://bandcamp.com/api/salesfeed/1/get_initial", timeout=1000
        )
    
    @patch("extract.requests.get")
    def test_extract_get_sales_information_timeout(self, mock_get):
        """Verify handling of a request timeout."""
        mock_get.side_effect = requests.exceptions.Timeout

        result = get_sales_information()
        assert result == {}
        mock_get.assert_called_once_with(
            "https://bandcamp.com/api/salesfeed/1/get_initial", timeout=1000
        )
    
    @patch("extract.requests.get")
    def test_extract_get_sales_information_connection_error(self, mock_get):
        """Verify handling of a connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError

        result = get_sales_information()
        assert result == {}
        mock_get.assert_called_once_with(
            "https://bandcamp.com/api/salesfeed/1/get_initial", timeout=1000
        )

class TestTransform:
    """Tests for the transform phase of the ETL process."""

    @pytest.mark.parametrize("unix_input,expected", [
        ("1633036800", "30-09-2021"),
        ("invalid", "None"),
    ])
    def test_transform_convert_unix_to_datetime(self, unix_input, expected):
        """Test conversion from Unix time to datetime."""
        assert convert_from_unix_to_datetime(unix_input) == expected

    @pytest.mark.parametrize("date_input,expected", [
    ("01-10-2021", "2021-10-01"),
    ("31-12-2020", "2020-12-31"),
    ("1 October 2021", "None"),
    ("invalid date", "None"),
    ("32-01-2021", "None"),
    ("01-13-2021", "None"),
    ("", "None"),
    ])

    def test_transform_convert_date_format(self, date_input, expected):
        """Test date format conversion."""
        assert convert_date_format(date_input) == expected

    @pytest.mark.parametrize("url_input,expected", [
        ("http://example.com", "http://example.com"),
        ("//example.com", "https://example.com"),
    ])
    def test_transform_convert_to_full_url(self, url_input, expected):
        """Test URL normalization."""
        assert convert_to_full_url(url_input) == expected

    @pytest.mark.parametrize("item_type,expected", [
        ("a", True),
        ("t", True),
        ("x", False),
    ])
    def test_transform_validate_album_and_track(self, item_type, expected):
        """Test validation of item types (album or track)."""
        assert validate_album_and_track(item_type) == expected

    @patch("transform.requests.get")
    def test_transform_get_genres_from_url(self, mock_get):
        """Test genre extraction from a URL."""
        mock_response = MagicMock(status_code=200, text='<a class="tag">Rock</a><a class="tag">Pop</a>')
        mock_get.return_value = mock_response
        locations = ["us", "rockville"]

        result = get_genres_from_url("//example.com", locations)
        assert set(result) == {"Rock", "Pop"}

        mock_get.side_effect = Exception("Network Error")
        assert get_genres_from_url("//example.com", locations) == []


    @patch("transform.requests.get")
    def test_transform_get_release_date_from_url(self, mock_get):
        """Test release date extraction from a URL."""
        mock_response = MagicMock(status_code=200, text='<meta name="description" content="released 1 October 2021">')
        mock_get.return_value = mock_response
        assert get_release_date_from_url("//example.com") == "2021-10-01"
        mock_response.text = '<meta name="description" content="No release date">'
        mock_get.return_value = mock_response
        assert get_release_date_from_url("//example.com") == ""
        mock_get.side_effect = Exception("Network Error")
        assert get_release_date_from_url("//example.com") == ""

    def test_transform_create_sales_dataframe_album(self):
        """Test DataFrame creation for album sales."""
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
        assert "release_type" in df.columns
        assert df.iloc[0]["release_type"] == "a"

    def test_transform_create_sales_dataframe_track(self):
        """Test DataFrame creation for album sales."""
        mock_sales_info = [
            {
                "release_type": "t",
                "release_description": "Sample Track",
                "album_title": "Mock Track",
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
        assert "release_type" in df.columns
        assert df.iloc[0]["release_type"] == "t"
    
    def test_transform_fill_out_album_and_track(self):
        test_data = {
            "release_type": ["a", "t", "a", "t", "x"],
            "other_column": [1, 2, 3, 4, 5],
        }
        test_df = pd.DataFrame(test_data)
        expected_data = {
            "release_type": ["album", "track", "album", "track", np.nan],
            "other_column": [1, 2, 3, 4, 5],
        }
        expected_df = pd.DataFrame(expected_data)
        fill_out_album_and_track(test_df)
        pd.testing.assert_frame_equal(test_df, expected_df)


class TestLoad:
    """Tests for the load phase of the ETL process."""

    @pytest.fixture(autouse=True)
    def mock_env(self, monkeypatch):
        """Mock database environment variables."""
        monkeypatch.setenv("DB_HOST", "mock_host")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_USER", "mock_user")
        monkeypatch.setenv("DB_PASSWORD", "mock_password")
        monkeypatch.setenv("DB_NAME", "mock_db")

    @pytest.fixture
    def mock_connection(self):
        """Provide a mocked database connection."""
        return MagicMock()

    @pytest.fixture
    def mock_cursor(self, mock_connection):
        """Provide a mocked database cursor."""
        cursor = MagicMock()
        mock_connection.cursor.return_value = cursor
        return cursor

    def test_load_get_connection(self):
        """Ensure database connection is established."""
        with patch("psycopg2.connect") as mock_connect:
            connection = get_connection()
            assert mock_connect.called
            assert connection is not None

    def test_load_get_cursor(self, mock_connection):
        """Ensure cursor is retrieved from the connection."""
        cursor = get_cursor(mock_connection)
        assert cursor is not None
        mock_connection.cursor.assert_called_once()


    def test_load_insert_country_existing(self, mock_cursor):
        """Test insertion of an existing country."""
        mock_cursor.fetchone.return_value = (True,)
        insert_country("TestCountry", mock_cursor)
        mock_cursor.execute.assert_called_once_with(
            "SELECT EXISTS (SELECT 1 FROM country WHERE country_name = %s);", ("TestCountry",)
        )

    def test_load_insert_country_new(self, mock_cursor):
        """Test insertion of a new country."""
        mock_cursor.fetchone.return_value = (False,)
        insert_country("NewCountry", mock_cursor)
        mock_cursor.execute.assert_any_call(
            "INSERT INTO country (country_name) VALUES (%s);", ("NewCountry",)
        )

    def test_load_insert_artist_new(self, mock_cursor):
        """Test insertion of a new artist."""
        mock_cursor.fetchone.return_value = None
        insert_artist("NewArtist", mock_cursor)
        assert mock_cursor.execute.call_count == 2

    def test_load_insert_genres_new(self, mock_cursor):
        """Test insertion of a new genre."""
        mock_cursor.fetchone.side_effect = [None, (1,)]
        genre_id = insert_genres("NewGenre", mock_cursor)
        assert genre_id == 1
    
    def test_load_get_id_from_table_found(self, mock_cursor):
        """Test retrieving an existing ID from the table."""
        mock_cursor.fetchone.return_value = (123,)
        result = get_id_from_table("TestValue", "test_table", mock_cursor)
        assert result == 123
        mock_cursor.execute.assert_called_once_with(
            "SELECT test_table_id FROM test_table WHERE test_table_name = %s;", 
            ("TestValue",)
        )

    def test_load_get_id_from_table_not_found(self, mock_cursor):
        """Test handling of a value not found in the table."""
        mock_cursor.fetchone.return_value = None
        result = get_id_from_table("NonExistentValue", "test_table", mock_cursor)
        assert result is None
        mock_cursor.execute.assert_called_once_with(
            "SELECT test_table_id FROM test_table WHERE test_table_name = %s;", 
            ("NonExistentValue",)
        )


    @patch.dict("os.environ", {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
        "DB_NAME": "test_db",
    })
    @patch("load.insert_country")
    @patch("load.insert_artist")
    @patch("load.insert_release")
    @patch("load.insert_genres")
    @patch("load.insert_release_genres")
    @patch("load.insert_sale_data")
    @patch("load.get_cursor")
    @patch("load.get_connection")
    def test_load_main_success(
        self,
        mock_get_connection,
        mock_get_cursor,
        mock_insert_sale_data,
        mock_insert_release_genres,
        mock_insert_genres,
        mock_insert_release,
        mock_insert_artist,
        mock_insert_country,
    ):
        """Test successful execution of the main load function."""
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_get_cursor.return_value = mock_cursor
        sales_df = pd.DataFrame({
            "country": ["USA", "Canada"],
            "artist_name": ["Artist1", "Artist2"],
            "release_name": ["Album1", "Album2"],
            "release_date": ["2023-01-01", "2023-02-01"],
            "release_type": ["Album", "Single"],
            "genres": [["Rock", "Pop"], ["Jazz"]],
            "amount_paid_usd": [9.99, 14.99],
            "sale_date": ["2023-03-01", "2023-03-02"],
        })
        main_load(sales_df)

        mock_insert_country.assert_has_calls([
            call("USA", mock_cursor),
            call("Canada", mock_cursor),
        ])
        mock_insert_artist.assert_has_calls([
            call("Artist1", mock_cursor),
            call("Artist2", mock_cursor),
        ])

    @patch("load.get_connection")
    @patch.dict(os.environ, {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "test_user",
        "DB_PASSWORD": "password",
        "DB_NAME": "test_db"
    })
    def test_load_main_failure(self, mock_get_connection):
        """Test the behavior of main_load when the connection fails."""
        mock_get_connection.return_value = None
        sales_df = pd.DataFrame({"column1": [1, 2, 3], "column2": ["A", "B", "C"]})
        with patch("logging.error") as mock_log_error:
            main_load(sales_df)
        mock_log_error.assert_called_with("Database connection failed. Exiting.")
