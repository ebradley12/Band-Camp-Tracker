"""Contains all the functions executing SQL script we will use for the alerts."""

import logging
from os import environ
import psycopg2
from psycopg2.extras import RealDictCursor
from utilities import convert_mins_to_sql_time, ALERT_INTERVAL, COMPARISON_PERIOD


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


def get_top_artist(cursor: RealDictCursor) -> str:
    """
    Get the top artist within the last comparison period.
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


def get_historic_top_artist(cursor: RealDictCursor) -> str:
    """
    get the top artist within the last comparison period,
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


def get_top_genre(cursor: RealDictCursor) -> str:
    """
    Get the top genre within the last comparison period.
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


def get_historic_top_genre(cursor: RealDictCursor) -> str:
    """
    Get the top genre within the last comparison period,
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


def get_genre_sales(cursor: RealDictCursor, genre: str) -> int:
    """
    Get the number of sales of a given genre within the last comparison period.
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


def get_historic_genre_sales(cursor: RealDictCursor, genre: str) -> int:
    """
    Get the number of sales of a given genre within the last comparison period,
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
