"""Streamlit Dashboard main script."""

import re
import streamlit as st
import psycopg2
from os import environ
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor


def get_connection() -> psycopg2.connect:
    """Returns connection to RDS."""
    return psycopg2.connect(
        dbname=environ.get("DB_NAME"),
        host=environ.get("DB_HOST"),
        user=environ.get("DB_USERNAME"),
        password=environ.get("DB_PASSWORD"),
        port=environ.get("DB_PORT")
    )


def get_cursor(conn) -> RealDictCursor:
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
    print("GENRES\n")
    genre_dict = {row['genre_name']: row['genre_id'] for row in genre_rows}

    return genre_dict


def add_subscriber_genres(conn, cursor, new_subscriber_id: int, genres_subscribed: list[int]) -> None:
    """Adds subscriber selected genres to RDS (subscriber_genre)."""
    for genre_id in genres_subscribed:
        cursor.execute("""
        INSERT INTO subscriber_genre (subscriber_id, genre_id)
        VALUES (%s, %s);
        """, (new_subscriber_id, genre_id))

        conn.commit()


def add_subscriber_info_to_db(email: str, alerts: bool, genres_subscribed: list[int]) -> None:
    """Adds subscriber info to RDS (subscriber)."""
    conn = get_connection()
    cursor = get_cursor(conn)

    cursor.execute("""
    INSERT INTO subscriber (subscriber_email, alerts)
    VALUES (%s, %s)
    RETURNING subscriber_id;
    """, (email, alerts))

    conn.commit()
    new_subscriber_id = cursor.fetchone()['subscriber_id']
    print(new_subscriber_id)

    add_subscriber_genres(conn, cursor, new_subscriber_id, genres_subscribed)


def convert_subscribed_genres_to_ids(genres_list: list[str], genres_dict: dict) -> list[int]:
    """Converts the subscribed genres from genre names to IDs."""
    subscribed_genre_ids = []
    for genre_name in genres_list:
        subscribed_genre_ids.append(genres_dict[genre_name])

    return subscribed_genre_ids


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
            st.success(f"Thank you for subscribing! Email: {email}")
            st.write("Daily Reports Subscription: Yes")
            st.write("Alerts Subscription:",
                     "Yes" if subscribe_alerts else "No")
            if selected_genres:
                st.write("Subscribed Genres:", ", ".join(selected_genres))
            else:
                st.write("Subscribed Genres: None")

            print(f"Email: {email}")
            print(f"Alerts: {subscribe_alerts}")
            print(f"Subscribed genres: {selected_genres}")

            selected_genre_ids = convert_subscribed_genres_to_ids(
                selected_genres, genres_dict)

            add_subscriber_info_to_db(
                email, subscribe_alerts, selected_genre_ids)


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


def insert_test_genre_data() -> None:
    """Inserts test genre data into RDS (genre)."""
    conn = get_connection()
    cursor = get_cursor(conn)

    test_genres = [
        "Action", "Adventure", "Comedy", "Drama", "Fantasy", "Horror", "Mystery",
        "Romance", "Science Fiction", "Thriller", "Western", "Animation", "Crime",
        "Documentary", "Family", "History", "Musical", "War", "Sport", "Biography"
    ]

    for genre in test_genres:
        cursor.execute(
            "INSERT INTO genre (genre_name) VALUES (%s);", (genre,))
        conn.commit()


if __name__ == "__main__":
    load_dotenv()
    run_dashboard()
