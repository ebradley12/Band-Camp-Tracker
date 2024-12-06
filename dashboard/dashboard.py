# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation
"""Streamlit Dashboard main script."""

import re
import logging
from os import environ
import streamlit as st
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from top_genre_sales import *


def get_connection() -> psycopg2.connect:
    """Returns connection to RDS."""
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


def get_genres_from_db() -> dict:
    """
    Returns a dictionary of all genres and their
    corresponding IDs.
    """
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""SELECT genre_name, genre_id FROM genre
                   ORDER BY genre_id;""")
    genre_rows = cursor.fetchall()
    genre_dict = {row['genre_name']: row['genre_id'] for row in genre_rows}

    return genre_dict


def add_subscriber_genres(conn: psycopg2.connect, cursor: RealDictCursor, new_subscriber_id: int,
                          genres_subscribed: list[int]) -> None:
    """Adds subscriber selected genres to RDS (subscriber_genre)."""
    for genre_id in genres_subscribed:
        cursor.execute("""
        INSERT INTO subscriber_genre (subscriber_id, genre_id)
        VALUES (%s, %s);
        """, (new_subscriber_id, genre_id))

        conn.commit()

    logging.info("Added subscriber genre preferences to RDS.")


def add_subscriber_info_to_db(email: str, alerts: bool, genres_subscribed: list[int]) -> bool:
    """Adds subscriber info to RDS (subscriber)."""
    conn = get_connection()
    cursor = get_cursor(conn)

    try:
        cursor.execute("""
        INSERT INTO subscriber (subscriber_email, alerts)
        VALUES (%s, %s)
        RETURNING subscriber_id;
        """, (email, alerts))

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
    Deletes all entries in subscriber_genre RDS table under the user
    being unsubscribed.
    """
    cursor.execute("""
    DELETE FROM subscriber_genre
    WHERE subscriber_id = %s;
    """, (subscriber_id,))

    conn.commit()
    logging.info("Deleted subscriber genre preferences from RDS.")


def unsubscribe_user(email: str) -> bool:
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
    if not subscriber_id:
        logging.warning(f"Could not find subscriber with given email {email}.")
        return False

    delete_subscriber_genres(subscriber_id['subscriber_id'], conn, cursor)
    logging.info("Successfully deleted subscriber info from RDS.")
    return True


def is_valid_email(email: str) -> bool:
    """Validates inputted user email address."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


def main_overview() -> None:
    """Creates main overview page on dashboard."""
    st.title("BandCamp Tracker: https://bandcamp.com/")
    st.write("Welcome to the Main Overview Page.")


def trends_page() -> None:
    """Creates trends page on dashboard."""
    st.title("Trends Page")
    st.write("Explore trends on this page.")
    target_date = st.date_input(
        "Select a date:", value=datetime.today()).strftime('%Y-%m-%d')
    connect = get_connection()

    sales_data = plot_sales_per_hour(connect, target_date)

    st.altair_chart(sales_data, use_container_width=True)


def report_download_page() -> None:
    """
    Creates reports page where user can
    download previous daily summary reports.
    """
    st.title("Report Download Page")
    st.write("Download reports from this page.")


def subscribe_page() -> None:
    """
    Creates subscribe page where users can subscribe
    to daily summary PDF reports and / or alerts about
    trends and genres via email.
    """
    st.title("Subscribe Page")
    st.write("Subscribe to daily reports and (optionally) alerts below.")

    # Email input
    email = st.text_input("Enter your email address:")

    # Checkbox for user alerts
    subscribe_alerts = st.checkbox("Subscribe to alerts")

    genres_dict = get_genres_from_db()
    genre_names = list(genres_dict.keys())

    # Multi-select for genres
    selected_genres = st.multiselect(
        "Select genres you want to receive updates about:",
        genre_names
    )

    # Submit button
    if st.button("Submit"):
        if not email:
            st.error("Please enter a valid email address.")
        elif not is_valid_email(email):
            st.error("Invalid email address, try again!")
        else:
            selected_genre_ids = convert_subscribed_genres_to_ids(
                selected_genres, genres_dict)

            add_subscriber = add_subscriber_info_to_db(
                email, subscribe_alerts, selected_genre_ids)

            if not add_subscriber:
                st.error("User with that email already exists!")
            else:
                st.success(f"Thank you for subscribing! Email: {email}")
                st.write("Daily Reports Subscription: Yes")
                st.write("Alerts Subscription:",
                         "Yes" if subscribe_alerts else "No")
                if selected_genres:
                    st.write("Subscribed Genres:", ", ".join(selected_genres))
                else:
                    st.write("Subscribed Genres: None")

                logging.info(f"""Successfully subscribed user with info:
                             Email: {email}
                             Alerts: {subscribe_alerts}
                             Subscribed genres: {selected_genres}""")

    st.write(
        "Alternatively, if you'd like to unsubscribe please enter your email and click below.")

    if st.button("Unsubscribe"):
        if not email:
            st.error("Please enter the email address you'd like to unsubscribe.")
        elif not is_valid_email(email):
            st.error("Invalid email address, try again!")
        else:
            unsubscribed = unsubscribe_user(email)
            if not unsubscribed:
                st.error(
                    "No user found with given email address, please try again.")
            else:
                st.success(
                    f"Successfully unsubscribed user with email: {email}")


def run_dashboard() -> None:
    """Sets up pages and runs the dashboard."""
    page_names_to_funcs = {
        "Main Overview": main_overview,
        "Trends": trends_page,
        "Report Download": report_download_page,
        "Subscribe": subscribe_page,
    }

    selected_page = st.sidebar.selectbox(
        "Navigate", page_names_to_funcs.keys())
    page_names_to_funcs[selected_page]()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )
    load_dotenv()
    run_dashboard()
