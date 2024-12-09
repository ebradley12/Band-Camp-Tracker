# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation

"""Database commands and functions for the subscribe/login page of the dashboard."""

import logging
from os import environ
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection() -> psycopg2.connect:
    """Returns connection to RDS."""
    load_dotenv()
    try:
        return psycopg2.connect(
            dbname=environ.get("DB_NAME"),
            host=environ.get("DB_HOST"),
            user=environ.get("DB_USER"),
            password=environ.get("DB_PASSWORD"),
            port=environ.get("DB_PORT")
        )
    except psycopg2.OperationalError as e:
        logging.warning("Failed to get connection to RDS.")
        raise Exception(e) from e


def get_cursor(conn: psycopg2.connect) -> RealDictCursor:
    """Returns cursor object to query RDS."""
    return conn.cursor(cursor_factory=RealDictCursor)


def get_genres_from_db() -> list[dict]:
    """
    Returns dictionaries of all genres and their
    corresponding IDs.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""SELECT genre_name, genre_id FROM genre
                   ORDER BY genre_id;""")
    genre_rows = cursor.fetchall()
    genre_name_to_id = {row['genre_name']: row['genre_id']
                        for row in genre_rows}
    genre_id_to_name = {row['genre_id']: row['genre_name']
                        for row in genre_rows}

    return genre_name_to_id, genre_id_to_name


def check_if_email_exists(email: str) -> bool:
    """
    Checks if a user with inputted email already exists in
    the database, returning a boolean value.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""SELECT count(*) from subscriber
                   WHERE subscriber_email = %s;""", (email,))
    email_exists = cursor.fetchone()
    count_email = email_exists['count']

    if count_email == 0:
        return True
    return False


def add_subscriber_genres(conn: psycopg2.connect, cursor: RealDictCursor, subscriber_id: int,
                          genres_subscribed: list[int]) -> None:
    """Adds subscriber's selected genres to RDS (subscriber_genre)."""
    for genre_id in genres_subscribed:
        cursor.execute("""
        INSERT INTO subscriber_genre (subscriber_id, genre_id)
        VALUES (%s, %s);
        """, (subscriber_id, genre_id))

        conn.commit()

    logging.info("Added subscriber genre preferences to RDS.")


def add_subscriber_info_to_db(email: str, alerts: bool, reports: bool,
                              genres_subscribed: list[int]) -> bool:
    """Adds subscriber's general info to RDS (subscriber)."""
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
        INSERT INTO subscriber (subscriber_email, subscribe_alert, subscribe_report)
        VALUES (%s, %s, %s)
        RETURNING subscriber_id;
        """, (email, alerts, reports))

    except psycopg2.errors.UniqueViolation:
        logging.warning(f"User with email {email} already exists!")
        return False

    conn.commit()
    new_subscriber_id = cursor.fetchone()['subscriber_id']

    if genres_subscribed:
        add_subscriber_genres(
            conn, cursor, new_subscriber_id, genres_subscribed)

    logging.info("Successfully added subscriber info to RDS.")
    return True


def convert_subscribed_genres_to_ids(genres_list: list[str], genres_dict: dict) -> list[int]:
    """Converts the subscribed genres from genre names to IDs."""
    subscribed_genre_ids = []
    for genre_name in genres_list:
        subscribed_genre_ids.append(genres_dict[genre_name])

    return subscribed_genre_ids


def delete_subscriber_genres(subscriber_id: int, conn: psycopg2.connect,
                             cursor: RealDictCursor) -> None:
    """
    Deletes all entries in 'subscriber_genre' RDS table under the ID of
    the user being unsubscribed.
    """
    cursor.execute("""
    DELETE FROM subscriber_genre
    WHERE subscriber_id = %s;
    """, (subscriber_id,))

    conn.commit()
    logging.info("Deleted subscriber genre preferences from RDS.")


def unsubscribe_user(email: str) -> None:
    """
    Unsubscribes a user with a given email address from
    all email services, removing their info from the database.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
    DELETE FROM subscriber
    WHERE subscriber_email = %s
    RETURNING subscriber_id;
    """, (email,))

    conn.commit()
    subscriber_id = cursor.fetchone()

    delete_subscriber_genres(subscriber_id['subscriber_id'], conn, cursor)
    logging.info("Successfully deleted subscriber info from RDS.")


def get_existing_subscriber_preferences(email: str) -> list:
    """
    Gets information of an existing user of the dashboard,
    such as their subscriber_id and email preferences.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
    SELECT subscriber_id, subscribe_alert, subscribe_report
    FROM subscriber
    WHERE subscriber_email = %s;""",
                   (email,))

    subscriber_details = cursor.fetchone()
    subscriber_id = int(subscriber_details['subscriber_id'])
    subscribe_alert = subscriber_details['subscribe_alert']
    subscribe_report = subscriber_details['subscribe_report']

    cursor.execute("""
    SELECT genre_id
    FROM subscriber_genre
    WHERE subscriber_id = %s;
    """, (subscriber_id,))

    subscribed_genre_rows = cursor.fetchall()

    subscribed_genre_ids = []
    if subscribed_genre_rows:
        for row in subscribed_genre_rows:
            subscribed_genre_ids.append(row['genre_id'])

    return subscriber_id, subscribe_alert, subscribe_report, subscribed_genre_ids


def update_subscribed_genres(sub_id: int, selected_genre_ids: list[int],
                             conn: psycopg2.connect, cursor: RealDictCursor) -> None:
    """
    Updates an existing subscriber's genre-specific alert preferences,
    by removing them and re-adding the new selection to the database.
    """
    delete_subscriber_genres(sub_id, conn, cursor)
    add_subscriber_genres(conn, cursor, sub_id, selected_genre_ids)


def update_existing_subscriber_info(sub_id: int, general_alerts: bool,
                                    daily_reports: bool, selected_genre_ids: list[int]) -> None:
    """
    Updates an existing subscriber's email and alert preferences
    on the database.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
    UPDATE subscriber
    SET subscribe_alert = %s,
        subscribe_report = %s
    WHERE subscriber_id = %s;
    """, (general_alerts, daily_reports, sub_id))
    conn.commit()

    if selected_genre_ids:
        update_subscribed_genres(sub_id, selected_genre_ids, conn, cursor)
