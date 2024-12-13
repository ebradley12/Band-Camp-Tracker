import pytest
from unittest.mock import MagicMock, patch
from alerts import (
    send_email,
    calculate_genre_sales_delta,
    send_top_artist_alert,
    send_top_genre_alert,
    send_chosen_genre_alert,
)

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("EMAIL_NAME", "test@example.com")
    monkeypatch.setenv("EMAIL_PASSWORD", "password123")

@patch("alerts.smtplib.SMTP")
def test_send_email(mock_smtp):
    send_email("recipient@example.com", "Test Subject", "Test Body")
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587)
    mock_smtp.return_value.starttls.assert_called_once()
    mock_smtp.return_value.login.assert_called_once_with(
        "test@example.com", "password123"
    )
    mock_smtp.return_value.sendmail.assert_called_once()

@patch("smtplib.SMTP", autospec=True)
def test_invalid_email_format(mock_smtp):
    send_email("invalid@@example.com", "Test Subject", "Test Body")
    mock_smtp.assert_called()

@patch("smtplib.SMTP")
def test_empty_subject(mock_smtp):
    mock_server = mock_smtp.return_value
    send_email("recipient@example.com", "", "Test Body")
    mock_server.sendmail.assert_called()

@patch("smtplib.SMTP")
def test_empty_body(mock_smtp):
    mock_server = mock_smtp.return_value
    send_email("recipient@example.com", "Test Subject", "")
    mock_server.sendmail.assert_called()


def test_calculate_genre_sales_delta():
    with patch("alerts.get_genre_sales") as mock_get_genre_sales, \
         patch("alerts.get_historic_genre_sales") as mock_get_historic_genre_sales:
        mock_get_genre_sales.return_value = 200
        mock_get_historic_genre_sales.return_value = 150
        mock_cursor = MagicMock()
        genre = "Rock"
        result = calculate_genre_sales_delta(mock_cursor, genre)
        assert result == pytest.approx(33.33, rel=0.01)
        mock_get_genre_sales.assert_called_once_with(mock_cursor, genre)
        mock_get_historic_genre_sales.assert_called_once_with(mock_cursor, genre)


def test_send_top_artist_alert_invalid_email():
    with patch("alerts.send_email") as mock_send_email:
        invalid_email = "invalid-email"
        artist = "New Top Artist"
        mock_send_email.side_effect = ValueError("Invalid email address")
        with pytest.raises(ValueError, match="Invalid email address"):
            send_top_artist_alert(invalid_email, artist)
        mock_send_email.assert_called_once()

def test_send_top_genre_alert():
    with patch("alerts.COMPARISON_PERIOD", 1440), patch("alerts.send_email") as mock_send_email:
        email = "<mailto:test@example.com|test@example.com>"
        genre = "Jazz"
        comparison_period_in_hours = 1440 / 60
        send_top_genre_alert(email, genre)
        expected_subject = "Top Genre Change Alert"
        expected_body = (
            f"The genre with the most sales in the last {comparison_period_in_hours} hours has changed!\n"
            f"The new number 1 genre is '{genre}'."
        )
        mock_send_email.assert_called_once_with(email, expected_subject, expected_body)

def test_send_chosen_genre_alert_no_top_artists():
    with patch("alerts.send_email") as mock_send_email:
        email = "<mailto:test@example.com|test@example.com>"
        genre = "Jazz"
        sales_delta = 10.0
        top_artists = []
        alert_interval = 60

        with patch("alerts.ALERT_INTERVAL", alert_interval):
            send_chosen_genre_alert(email, genre, sales_delta, top_artists)

            expected_subject = "Jazz Growth Alert"
            expected_body = (
                f"Your subscribed genre 'Jazz' has seen a 10.0% increase in sales in the last 60 minutes!\n\n"
                f"The current top selling artists in Jazz are:\n"
            )

            mock_send_email.assert_called_once_with(email, expected_subject, expected_body)