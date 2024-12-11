# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation
"""Streamlit Dashboard main script."""

import re
import logging
import time
import streamlit as st
from dotenv import load_dotenv
from embeddings import show_embeds
from subscribe_page_commands import (
    get_genres_from_db,
    check_if_email_exists,
    add_subscriber_info_to_db,
    convert_subscribed_genres_to_ids,
    unsubscribe_user,
    get_existing_subscriber_preferences,
    update_existing_subscriber_info
)


def is_valid_email(email: str) -> bool:
    """Validates inputted user email address."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


def main_overview() -> None:
    """Creates main overview page on dashboard."""
    st.title("BandCamp Tracker")
    st.write("https://bandcamp.com/")
    st.write("Welcome to the Main Overview Page.")


def trends_page() -> None:
    """Creates trends page on dashboard."""
    st.title("Trends Page")
    st.write("Explore trends on this page.")
    show_embeds()


def report_download_page() -> None:
    """
    Creates reports page where user can
    download previous daily summary reports.
    """
    st.title("Report Download Page")
    st.write("Download reports from this page.")


def subscribe_page() -> None:
    """
    Implements a 'Subscribe' page with a login portal.
    """
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    st.title("Subscribe Page")
    st.write("Please enter your email to login / subscribe.")

    email = st.text_input("Enter your email address:")
    if st.button("Login / Subscribe"):
        if not email:
            st.error("Please enter a valid email address.")
        elif not is_valid_email(email):
            st.error("Invalid email address, try again!")
        else:
            st.session_state.logged_in = True

    if st.session_state.logged_in:
        st.title("Set Your Preferences")
        st.write(f"Logged in as: {email}")

        new_user = check_if_email_exists(email)
        genre_name_to_id, genre_id_to_name = get_genres_from_db()
        genre_names = list(genre_name_to_id.keys())

        if new_user:
            st.success("New user account created!")
            sub_id = False
            general_alerts_check = False
            daily_reports_check = False
            sub_genre_ids = []
        else:
            st.success("Welcome back!")
            sub_id, general_alerts_check, daily_reports_check, sub_genre_ids = get_existing_subscriber_preferences(
                email)

        genre_names_selected = []

        if sub_genre_ids:
            genre_alerts_check = True
            for genre_id in sub_genre_ids:
                genre_names_selected.append(genre_id_to_name[genre_id])
        else:
            genre_alerts_check = False

            # Checkboxes for email preferences
        daily_reports = st.checkbox(
            "Subscribe to daily summary reports", value=daily_reports_check)
        general_alerts = st.checkbox(
            "Subscribe to general alerts", value=general_alerts_check)
        genre_alerts = st.checkbox(
            "Subscribe to alerts for specific genres", value=genre_alerts_check)

        if genre_alerts:
            # Multiselect for genre-specific alerts
            selected_genres = st.multiselect(
                "Select your preferred genres:",
                genre_names,
                default=genre_names_selected
            )

        if st.button("Save Preferences"):
            if genre_alerts:
                if selected_genres:
                    selected_genre_ids = convert_subscribed_genres_to_ids(
                        selected_genres, genre_name_to_id)
                else:
                    selected_genre_ids = []
            else:
                selected_genre_ids = []

            if new_user:
                add_subscriber_info_to_db(
                    email, general_alerts, daily_reports, selected_genre_ids)
                new_user = False
            else:
                update_existing_subscriber_info(
                    sub_id, general_alerts, daily_reports, selected_genre_ids)

            st.success("Preferences saved successfully!")

        st.write("")
        st.write("Alternatively, you can unsubscribe below")
        if st.button("Unsubscribe"):
            unsubscribe_user(email)
            st.success(f"Unsubscribed user: {email} successfully")
            # Allows time for user to see unsubscribe message before returning
            # screen to initial state
            time.sleep(2)
            st.session_state.logged_in = False
            st.rerun()  # Returns screen to initial state


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
