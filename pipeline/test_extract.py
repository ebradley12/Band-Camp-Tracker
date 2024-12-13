"""Tests for the extract script."""

from unittest.mock import patch, Mock
import pytest
from extract import get_sales_information


@pytest.fixture
def event_example():
    """An example of an event that would be 
    returned from the API"""
    event = {'event_type': 'sale', 'utc_date': 1733149631.11862,
             'items':
             [{'utc_date': 1733149631.946907, 'artist_name': 'Brokenears',
               'item_type': 't', 'item_description':
               "On It's Way (Unreleased Brokenears Remix)",
               'album_title': "On It's Way EP",
               'slug_type': 't', 'track_album_slug_text': None,
               'currency': 'EUR', 'amount_paid': 2.5,
               'item_price': 2.5, 'amount_paid_usd': 2.63,
               'country': 'United Kingdom', 'art_id': 1845377130,
               'releases': None, 'package_image_id': None,
               'url': '//houseandchips.bandcamp.com/track/on-its-way',
               'country_code': 'gb', 'amount_paid_fmt': '€2.50',
               'art_url': 'https://f4.bcbits.com/img/a1845377130_7.jpg'}]}

    return event


@patch('requests.get')
def test_get_sales_information_success(mock_get, event_example):
    """Tests results on a sucessful request"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'feed_data':
                                       {'start_date': 1733154060, 'end_date': 1733154660,
                                        'data_delay_sec': 120, 'events': event_example,
                                        'server_time': 173315468}}
    mock_get.return_value = mock_response

    result = get_sales_information()

    assert list(result.keys()) == ['feed_data']
    assert list(result['feed_data'].keys()) == ['start_date', 'end_date',
                                                'data_delay_sec', 'events', 'server_time']
    mock_get.assert_called_once_with(
        "https://bandcamp.com/api/salesfeed/1/get_initial")


@patch('requests.get')
def test_get_sales_information_failure(mock_get):
    """Test results on a failure"""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    result = get_sales_information()

    assert result == {}
    mock_get.assert_called_once_with(
        "https://bandcamp.com/api/salesfeed/1/get_initial")
