"""The main script for generating and sending artist and genre based alerts."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from os import environ
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from utilities import config_log, validate_env_vars, ALERT_INTERVAL, COMPARISON_PERIOD, GENRE_NOTIFICATION_THRESHOLD
from queries import get_connection, get_cursor, get_general_subscriber_emails, get_genre_subscriber_emails, get_subscribed_genres, get_top_artist, get_historic_top_artist, get_top_genre, get_historic_top_genre, get_genre_top_artists, get_genre_sales, get_historic_genre_sales


def send_email(recipient: str, subject: str, body: str) -> None:
    """
    Sends an email from the bandcamp notifier email to a given email.
    """
    sender_email = environ.get("EMAIL_NAME")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, environ.get("EMAIL_PASSWORD"))

        server.sendmail(sender_email, recipient, message.as_string())

    except smtplib.SMTPConnectError as e:
        logging.error("Failed to send email: %s", e)
    finally:
        server.quit()


def send_top_artist_alert(email: str, artist: str) -> None:
    """
    Sends an alert about the top genre changing to the given email.
    """
    email_subject = "Top Artist Change Alert"

    email_body = f"The artist with the most sales in the last {COMPARISON_PERIOD/60} hours has changed!\nThe new number 1 artist is {artist}."

    send_email(email, email_subject, email_body)


def send_top_genre_alert(email: str, genre: str) -> None:
    """
    Sends an alert about the top genre changing to the given email.
    """

    email_subject = "Top Genre Change Alert"

    email_body = f"The genre with the most sales in the last {COMPARISON_PERIOD/60} hours has changed!\nThe new number 1 genre is '{genre}'."

    send_email(email, email_subject, email_body)


def send_chosen_genre_alert(email: str, genre: str, sales_delta: float, top_artists: dict) -> None:
    """
    Sends an alert about the subscribed genre changing to the given email.
    """
    email_subject = f"{genre.title()} Growth Alert"

    top_artists_formatted = ""
    for artist in top_artists:
        top_artists_formatted += f"  - {artist['artist_name']}: ${artist['total_sales']:.2f}\n"
    email_body = f"Your subscribed genre '{genre}' has seen a {sales_delta:.1f}% increase in sales in the last {ALERT_INTERVAL} minutes!\n\nThe current top selling artists in {genre} are:\n{top_artists_formatted}"
    send_email(email, email_subject, email_body)


def calculate_genre_sales_delta(cursor, genre) -> float:
    """
    Calculates the percentage difference in sales numbers for a given genre
    within the last alert interval compared to the comparison period.
    """
    recent_sales = get_genre_sales(cursor, genre)
    historic_sales = get_historic_genre_sales(cursor, genre)

    sales_delta = 100 * (recent_sales - historic_sales) / historic_sales

    return sales_delta


def alert_top_artist_change(cursor: RealDictCursor) -> None:
    """
    Checks if the historical top artist has recently changed,
    and sends an alert to all subscribers if it has.
    """
    top_artist = get_top_artist(cursor)
    historic_top_artist = get_historic_top_artist(cursor)
    sub_emails = get_general_subscriber_emails(cursor)

    logging.info("Checking for change in top artist")

    if top_artist != historic_top_artist:
        logging.info("Top artist has changed: Alerting subscribers")
        for email in sub_emails:
            send_top_artist_alert(email, top_artist)
        logging.info("All top artist change alerts sent successfully")

    else:
        logging.info("No change detected in top artist")


def alert_top_genre_change(cursor: RealDictCursor) -> None:
    """
    Checks if the historical top genre has recently changed,
    and sends an alert to all subscribers if it has.
    """
    top_genre = get_top_genre(cursor)
    historic_top_genre = get_historic_top_genre(cursor)
    sub_emails = get_general_subscriber_emails(cursor)

    logging.info("Checking for change in top genre")

    if top_genre != historic_top_genre:
        logging.info("Top genre has changed: Alerting subscribers")
        for email in sub_emails:
            send_top_genre_alert(email, top_genre)
        logging.info("All top genre change alerts sent successfully")

    else:
        logging.info("No change detected in top genre")


def alert_subscribed_genres(cursor: RealDictCursor) -> None:
    """
    Checks each subscribed genre for if it has grown in popularity
    past the notification threshold recently, and sends alerts
    for each one that has to those who are subscribed, along with
    the current top artists for that genre.
    """
    logging.info(
        "Checking for increases in subscribed genre sales above the alert threshold")

    genres = get_subscribed_genres(cursor)
    for genre in genres:
        sales_delta = calculate_genre_sales_delta(cursor, genre)
        if sales_delta > GENRE_NOTIFICATION_THRESHOLD:
            logging.info(
                "Alert threshold surpassed for '%s': Alerting subscribers", genre)
            top_artists = get_genre_top_artists(cursor, genre)
            emails = get_genre_subscriber_emails(cursor, genre)
            for email in emails:
                send_chosen_genre_alert(email, genre, sales_delta, top_artists)
            logging.info("All '%s' alerts sent successfully", genre)
        else:
            logging.info(
                "'%s' sales did not surpass the alert threshold", genre)


def main() -> None:
    """The main function that generates and sends all alerts"""
    load_dotenv()
    validate_env_vars()
    config_log()
    db_conn = get_connection()
    db_cursor = get_cursor(db_conn)
    alert_top_artist_change(db_cursor)
    alert_top_genre_change(db_cursor)
    alert_subscribed_genres(db_cursor)
    db_conn.close()


if __name__ == "__main__":
    main()
