"""The script for generating and sending artist and genre based alerts."""

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import logging
from os import environ
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv


# The period of time between checking for alerts in minutes
ALERT_INTERVAL = 60
# The period of time we use to assess historic trends in minutes
COMPARISON_PERIOD = 2880
# The percentage value a genre has to have grown in popularity before alerting the user
GENRE_NOTIFICATION_THRESHOLD = 20


def config_log() -> None:
    """
    Terminal logs configuration.
    """
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )


def validate_env_vars() -> None:
    """
    Raises an error if any environment variables are missing.
    """
    required_vars = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing_vars = [var for var in required_vars if var not in environ]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {missing_vars}")


def get_connection() -> psycopg2.connect:
    """
    Returns connection to RDS.
    """
    try:
        return psycopg2.connect(
            dbname=environ.get("DB_NAME"),
            host=environ.get("DB_HOST"),
            user=environ.get("DB_USER"),
            password=environ.get("DB_PASSWORD"),
            port=environ.get("DB_PORT")
        )
    except psycopg2.OperationalError as e:
        logging.error("Failed to get connection to RDS: %s", e)
        raise


def get_cursor(conn: psycopg2.connect) -> RealDictCursor:
    """
    Returns cursor object to query RDS.
    """
    return conn.cursor(cursor_factory=RealDictCursor)


def get_general_subscriber_emails(cursor: RealDictCursor) -> list[str]:
    """
    Returns a list of all emails that are signed up to general alerts.
    """
    logging.info("Fetching alert subscriber emails")

    query = """
            SELECT subscriber_email 
            FROM subscriber
            WHERE subscribe_alert = true;
            """

    try:
        cursor.execute(query)
        sub_emails = cursor.fetchall()
        sub_emails = [email["subscriber_email"] for email in sub_emails]

    except psycopg2.Error as e:
        logging.error("Failed to fetch emails: %s", e)
        raise

    logging.info("Emails fetched successfully")

    return sub_emails


def get_genre_subscriber_emails(cursor: RealDictCursor, genre: str) -> list[str]:
    """
    Returns a list of all emails that are signed up to alerts for a specific genre.
    """
    logging.info("Fetching '%s' subscriber emails", genre)

    query = f"""
            SELECT subscriber_email
            FROM subscriber AS s
            JOIN subscriber_genre AS sg ON s.subscriber_id = sg.subscriber_id
            JOIN genre AS g ON sg.genre_id = g.genre_id
            WHERE g.genre_name = '{genre}';
            """

    try:
        cursor.execute(query)
        sub_emails = cursor.fetchall()
        sub_emails = [email["subscriber_email"] for email in sub_emails]

    except psycopg2.Error as e:
        logging.error("Failed to fetch emails: %s", e)
        raise

    logging.info("Emails fetched successfully")

    return sub_emails


def get_subscribed_genres(cursor: RealDictCursor) -> list[str]:
    """
    Returns a list of all genres that have at least one subscriber.
    """
    logging.info("Fetching subscribed genres list")

    query = """
            SELECT DISTINCT g.genre_name
            FROM subscriber_genre AS sg
            JOIN genre AS g ON sg.genre_id = g.genre_id;
            """

    try:
        cursor.execute(query)
        genres = cursor.fetchall()
        genres = [genre["genre_name"] for genre in genres]

    except psycopg2.Error as e:
        logging.error("Failed to fetch genres: %s", e)
        raise

    logging.info("Genres fetched successfully")
    return genres


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


def send_chosen_genre_alert(email: str, genre: str, sales_delta: float) -> None:
    """
    Sends an alert about the subscribed genre changing to the given email.
    """
    email_subject = f"{genre.title()} Growth Alert"

    email_body = f"Your subscribed genre '{genre}' has seen a {sales_delta:.1f}% increase in sales in the last {ALERT_INTERVAL} minutes!"
    send_email(email, email_subject, email_body)


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


def convert_mins_to_sql_time(minutes: int) -> str:
    """
    Takes a time value in minutes and converts it into a
    string of the time interval it represents backwards from now,
    in a format that an SQL query can understand.
    """
    base_string = "NOW() - INTERVAL "

    if minutes < 1:
        raise ValueError("All config times must be larger than one minute")

    time_string = f"'{minutes} minutes'"

    if minutes == 1:
        time_string = time_string[:-1]

    return base_string + time_string


def query_top_artist(cursor: RealDictCursor) -> str:
    """
    Query the top artist within the last comparison period.
    """
    comp_period = convert_mins_to_sql_time(COMPARISON_PERIOD)

    query = f"""
            SELECT a.artist_name
            FROM sale AS s
            JOIN release AS r ON s.release_id = r.release_id
            JOIN artist AS a ON r.artist_id = a.artist_id
            WHERE s.sale_date >= {comp_period}
            GROUP BY a.artist_name
            ORDER BY COUNT(s.sale_id) DESC
            LIMIT 1;
            """

    logging.info("Fetching top artist")

    try:
        cursor.execute(query)
        top_artist = cursor.fetchone()

    except psycopg2.Error as e:
        logging.error("Failed to fetch top artist: %s", e)
        raise

    logging.info("Top artist fetched successfully")

    return top_artist["artist_name"]


def query_historic_top_artist(cursor: RealDictCursor) -> str:
    """
    Query the top artist within the last comparison period,
    excluding the last alert interval to assess the historic top.
    """
    comp_period = convert_mins_to_sql_time(COMPARISON_PERIOD)
    alert_interval = convert_mins_to_sql_time(ALERT_INTERVAL)

    query = f"""
            SELECT a.artist_name
            FROM sale AS s
            JOIN release AS r ON s.release_id = r.release_id
            JOIN artist AS a ON r.artist_id = a.artist_id
            WHERE s.sale_date BETWEEN {comp_period} AND {alert_interval}
            GROUP BY a.artist_name
            ORDER BY COUNT(s.sale_id) DESC
            LIMIT 1;
            """

    logging.info("Fetching historic top artist")

    try:
        cursor.execute(query)
        top_artist = cursor.fetchone()

    except psycopg2.Error as e:
        logging.error("Failed to fetch historic top artist: %s", e)
        raise

    logging.info("Historic top artist fetched successfully")

    return top_artist["artist_name"]


def query_top_genre(cursor: RealDictCursor) -> str:
    """
    Query the top genre within the last comparison period.
    """
    comp_period = convert_mins_to_sql_time(COMPARISON_PERIOD)

    query = f"""
            SELECT g.genre_name
            FROM genre AS g
            JOIN release_genre AS rg ON g.genre_id = rg.genre_id
            JOIN release AS r ON r.release_id = rg.release_id
            JOIN sale AS s ON s.release_id = r.release_id
            WHERE s.sale_date >= {comp_period}
            GROUP BY g.genre_name
            ORDER BY COUNT(s.sale_id) DESC
            LIMIT 1;
            """

    logging.info("Fetching top genre")

    try:
        cursor.execute(query)
        top_genre = cursor.fetchone()

    except psycopg2.Error as e:
        logging.error("Failed to fetch top genre: %s", e)
        raise

    logging.info("Top genre fetched successfully")

    return top_genre["genre_name"]


def query_historic_top_genre(cursor: RealDictCursor) -> str:
    """
    Query the top genre within the last comparison period,
    excluding the last alert interval to assess the historic top.
    """
    comp_period = convert_mins_to_sql_time(COMPARISON_PERIOD)
    alert_interval = convert_mins_to_sql_time(ALERT_INTERVAL)

    query = f"""
            SELECT g.genre_name
            FROM genre AS g
            JOIN release_genre AS rg ON g.genre_id = rg.genre_id
            JOIN release AS r ON r.release_id = rg.release_id
            JOIN sale AS s ON s.release_id = r.release_id
            WHERE s.sale_date BETWEEN {comp_period} AND {alert_interval}
            GROUP BY g.genre_name
            ORDER BY COUNT(s.sale_id) DESC
            LIMIT 1;
            """

    logging.info("Fetching historic top genre")

    try:
        cursor.execute(query)
        top_genre = cursor.fetchone()

    except psycopg2.Error as e:
        logging.error("Failed to fetch historic top genre: %s", e)
        raise

    logging.info("Historic top genre fetched successfully")

    return top_genre["genre_name"]


def query_genre_sales(cursor: RealDictCursor, genre: str) -> int:
    """
    Query the number of sales of a given genre within the last comparison period.
    """
    comp_period = convert_mins_to_sql_time(COMPARISON_PERIOD)

    query = f"""
            SELECT COUNT(s.sale_id)
            FROM sale AS s
            JOIN release AS r ON s.release_id = r.release_id
            JOIN release_genre AS rg ON r.release_id = rg.release_id
            JOIN genre AS g ON rg.genre_id = g.genre_id
            WHERE s.sale_date >= {comp_period}
            AND g.genre_name = '{genre}';
            """

    logging.info("Fetching number of '%s' sales", genre)

    try:
        cursor.execute(query)
        sales = cursor.fetchone()

    except psycopg2.Error as e:
        logging.error("Failed to fetch number of '%s' sales: %s", genre, e)
        raise

    logging.info("Number of '%s' sales fetched successfully", genre)

    return sales["count"]


def query_historic_genre_sales(cursor: RealDictCursor, genre: str) -> int:
    """
    Query the number of sales of a given genre within the last comparison period,
    excluding the last alert interval to assess the historic value.
    """
    comp_period = convert_mins_to_sql_time(COMPARISON_PERIOD)
    alert_interval = convert_mins_to_sql_time(ALERT_INTERVAL)

    query = f"""
            SELECT COUNT(s.sale_id)
            FROM sale AS s
            JOIN release AS r ON s.release_id = r.release_id
            JOIN release_genre AS rg ON r.release_id = rg.release_id
            JOIN genre AS g ON rg.genre_id = g.genre_id
            WHERE s.sale_date BETWEEN {comp_period} AND {alert_interval}
            AND g.genre_name = '{genre}';
            """

    logging.info("Fetching historic number of '%s' sales", genre)

    try:
        cursor.execute(query)
        sales = cursor.fetchone()

    except psycopg2.Error as e:
        logging.error(
            "Failed to fetch historic number of '%s' sales: %s", genre, e)
        raise

    logging.info("Historic number of '%s' sales fetched successfully", genre)

    return sales["count"]


def alert_top_artist_change(cursor: RealDictCursor) -> None:
    """
    Checks if the historical top artist has recently changed,
    and sends an alert to all subscribers if it has.
    """
    top_artist = query_top_artist(cursor)
    historic_top_artist = query_historic_top_artist(cursor)
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
    top_genre = query_top_genre(cursor)
    historic_top_genre = query_historic_top_genre(cursor)
    sub_emails = get_general_subscriber_emails(cursor)

    logging.info("Checking for change in top genre")

    if top_genre != historic_top_genre:
        logging.info("Top genre has changed: Alerting subscribers")
        for email in sub_emails:
            send_top_genre_alert(email, top_genre)
        logging.info("All top genre change alerts sent successfully")

    else:
        logging.info("No change detected in top genre")


def calculate_genre_sales_delta(cursor, genre) -> float:
    """
    Calculates the percentage difference in sales numbers for a given genre
    within the last alert interval compared to the comparison period.
    """
    recent_sales = query_genre_sales(cursor, genre)
    historic_sales = query_historic_genre_sales(cursor, genre)

    sales_delta = 100 * (recent_sales - historic_sales) / historic_sales

    return sales_delta


def alert_subscribed_genres(cursor: RealDictCursor) -> None:
    """
    Checks each subscribed genre for if it has grown in popularity
    past the notification threshold recently, and sends alerts
    for each one that has to those who are subscribed.
    """
    logging.info(
        "Checking for increases in subscribed genre sales above the alert threshold")

    genres = get_subscribed_genres(cursor)
    for genre in genres:
        sales_delta = calculate_genre_sales_delta(cursor, genre)
        if sales_delta > GENRE_NOTIFICATION_THRESHOLD:
            logging.info(
                "Alert threshold surpassed for '%s': Alerting subscribers", genre)
            emails = get_genre_subscriber_emails(cursor, genre)
            for email in emails:
                send_chosen_genre_alert(email, genre, sales_delta)
            logging.info("All '%s' alerts sent successfully", genre)
        else:
            logging.info(
                "'%s' sales did not surpass the alert threshold", genre)


def main() -> None:
    """The main function that generates and sends all alerts"""
    load_dotenv()
    config_log()
    db_conn = get_connection()
    db_cursor = get_cursor(db_conn)
    alert_top_artist_change(db_cursor)
    alert_top_genre_change(db_cursor)
    alert_subscribed_genres(db_cursor)
    db_conn.close()


if __name__ == "__main__":
    main()
