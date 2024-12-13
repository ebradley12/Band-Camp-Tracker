# pylint: disable=no-member
# pylint: disable=logging-fstring-interpolation
"""Streamlit Dashboard main script."""
import re
import logging
import time
from os import environ
from datetime import datetime, date, timedelta
import streamlit as st
import boto3
from dotenv import load_dotenv
from subscribe_page_commands import (
    get_genres_from_db,
    check_if_email_exists,
    add_subscriber_info_to_db,
    convert_subscribed_genres_to_ids,
    unsubscribe_user,
    get_existing_subscriber_preferences,
    update_existing_subscriber_info
)

from streamlit_graphs.queries import (
    get_connection,
    get_top_genre,
    get_top_track,
    get_top_album,
    get_top_artist,
    get_total_sales,
    get_top_country,
)

from streamlit_graphs.release_type_chart import visualise_release_types
from streamlit_graphs.sales_by_country import visualise_country_sales
from streamlit_graphs.sales_over_time import visualise_sales_per_hour
from streamlit_graphs.top_artist_sales import visualise_sales_per_artist_over_time
from streamlit_graphs.top_genre_sales import visualise_genre_sales

from dashboard_formatting import glamourize_dashboard
from embeddings import show_embeds
import os

image_path = os.path.abspath("BandScout_logo.png")


def is_valid_email(email: str) -> bool:
    """Validates inputted user email address."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


def main_overview() -> None:
    """Creates main overview page on dashboard."""
    connection = get_connection()
    st.title("Welcome to BandScout")

    st.header("Top Metrics Today")

    col1, col2, col3 = st.columns([0.33, 0.33, 0.33])
    with col1:
        total_sales = get_total_sales(connection)
        st.markdown(
            "<p style='font-size:20px; font-weight:bold; word-wrap: break-word;'>💵 Total Sales</p>", unsafe_allow_html=True)
        st.markdown(f"""<p style='font-size:24px; font-weight:normal; word-wrap: break-word;'>${
                    total_sales:,.2f}</p>""", unsafe_allow_html=True)
    with col2:
        top_genre = get_top_genre(connection)
        if not top_genre.empty:
            st.markdown(
                "<p style='font-size:20px; font-weight:bold; word-wrap: break-word;'>🎼 Top Genre</p>", unsafe_allow_html=True)
            st.markdown(f"""<p style='font-size:24px; font-weight:normal; word-wrap: break-word;'>{top_genre['genre_name'].iloc[0]}</p>""",
                        unsafe_allow_html=True)

    with col3:
        top_country = get_top_country(connection)
        if not top_country.empty:
            st.markdown(
                "<p style='font-size:20px; font-weight:bold; word-wrap: break-word;'>🌍 Top Country</p>", unsafe_allow_html=True)
            st.markdown(f"""<p style='font-size:24px; font-weight:normal; word-wrap: break-word;'>{top_country['country_name'].iloc[0]}</p>""",
                        unsafe_allow_html=True)

    st.divider()

    col4, col5, col6 = st.columns([0.33, 0.33, 0.33])
    with col4:
        top_artist = get_top_artist(connection)
        if not top_artist.empty:
            st.markdown(
                "<p style='font-size:20px; font-weight:bold; word-wrap: break-word;'>🎤 Top Artist</p>", unsafe_allow_html=True)
            st.markdown(f"""<p style='font-size:24px; font-weight:normal; word-wrap: break-word;'>{top_artist['artist_name'].iloc[0]}</p>""",
                        unsafe_allow_html=True)
    with col5:
        top_track = get_top_track(connection)
        if not top_track.empty:
            st.markdown(
                "<p style='font-size:20px; font-weight:bold; word-wrap: break-word;'>🎵 Top Track</p>", unsafe_allow_html=True)
            st.markdown(f"""<p style='font-size:24px; font-weight:normal; word-wrap: break-word;'>{top_track['release_name'].iloc[0]}</p>""",
                        unsafe_allow_html=True)

    with col6:
        top_album = get_top_album(connection)
        if not top_album.empty:
            st.markdown(
                "<p style='font-size:20px; font-weight:bold; word-wrap: break-word;'>💽 Top Album</p>", unsafe_allow_html=True)
            st.markdown(f"""<p style='font-size:24px; font-weight:normal; word-wrap: break-word;'>{top_album['album_name'].iloc[0]}</p>""",
                        unsafe_allow_html=True)

    st.divider()
    with st.container():
        st.subheader("Freshest Tracks")
        show_embeds()

    connection.close()


def trends_page() -> None:
    """Creates trends page on dashboard."""
    st.title(" 📈 Trends Page")

    connection = get_connection()

    date_range = st.date_input(
        "Select Date or Date Range:",
        value=(date(2024, 12, 5), date.today()),
        min_value=date(2024, 12, 5),
        max_value=date.today()
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    if isinstance(start_date, tuple):
        start_date = start_date[0]
    if isinstance(end_date, tuple):
        end_date = end_date[0]

    visualise_sales_per_artist_over_time(connection, start_date, end_date)
    visualise_genre_sales(connection, start_date, end_date)
    visualise_country_sales(connection, start_date, end_date)
    visualise_sales_per_hour(connection, start_date, end_date)
    visualise_release_types(connection)

    connection.close()


def download_reports_from_s3(s3: boto3.client, bucket_name: str, subfolder: str) -> list[str]:
    """
    Downloads PDF reports from S3 bucket 
    onto local directory 'daily_reports',
    returning a list of filenames downloaded.
    """
    downloaded_reports = []
    for object_name in s3.list_objects(Bucket=bucket_name, Prefix=subfolder)['Contents']:
        object_key = object_name['Key']
        report_filename = object_key.split("/")[1]
        s3.download_file(bucket_name, object_key,
                         f"daily_reports/{report_filename}")
        downloaded_reports.append(report_filename)

    return downloaded_reports


def report_download_page() -> None:
    """
    Creates reports page where user can
    download previous daily summary reports.
    """
    st.title(" 📝 Reports")
    st.write("Download reports from this page.")

    default_start_date = date(2024, 12, 5)
    default_end_date = date.today() - timedelta(days=1)

    date_range = st.date_input(
        "Select a date range:",
        value=(default_start_date, default_end_date),
        min_value=date(2024, 12, 5),
        max_value=default_end_date
    )

    if isinstance(date_range, tuple):
        if len(date_range) == 2:
            start_date, end_date = date_range
            st.write(f"Start Date: {start_date}")
            st.write(f"End Date: {end_date}")
        else:

            start_date = date_range[0]
            end_date = date_range[0]
            st.write(f"Selected Date: {start_date}")

        s3 = boto3.client('s3', aws_access_key_id=environ.get(
            "ACCESS_KEY_ID"), aws_secret_access_key=environ.get("SECRET_ACCESS_KEY"))
        downloaded_reports = download_reports_from_s3(
            s3, environ.get("S3_BUCKET"), environ.get("S3_FOLDER"))

        if downloaded_reports:
            reports_in_range = False
            for report_filename in downloaded_reports:
                report_date = report_filename.split("_")[3].split(".")[0]
                report_format_date = datetime.strptime(
                    report_date, "%Y-%m-%d").date()

                if start_date <= report_format_date <= end_date:
                    reports_in_range = True
                    with open(f"daily_reports/{report_filename}", 'rb') as report:
                        report_bytes = report.read()

                    st.download_button(
                        label=report_filename,
                        data=report_bytes,
                        file_name=report_filename,
                        mime="application/octet-stream"
                    )

        if not reports_in_range:
            st.info("No reports available in the selected date range.")
    else:
        st.error("Please select a valid date range.")


def subscribe_page() -> None:
    """
    Implements a 'Subscribe' page with a login portal.
    """
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    st.title("✉️ Subscribe")
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
            sub_id, general_alerts_check, daily_reports_check,
            sub_genre_ids = get_existing_subscriber_preferences(
                email)

        genre_names_selected = []

        if sub_genre_ids:
            genre_alerts_check = True
            for genre_id in sub_genre_ids:
                genre_names_selected.append(genre_id_to_name[genre_id])
        else:
            genre_alerts_check = False

        daily_reports = st.checkbox(
            "Subscribe to daily summary reports", value=daily_reports_check)
        general_alerts = st.checkbox(
            "Subscribe to general alerts", value=general_alerts_check)
        genre_alerts = st.checkbox(
            "Subscribe to alerts for specific genres", value=genre_alerts_check)

        if genre_alerts:
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
            time.sleep(2)
            st.session_state.logged_in = False
            st.rerun()


def run_dashboard() -> None:
    """Sets up pages and runs the dashboard."""
    glamourize_dashboard()
    load_dotenv()

    st.markdown(
        """
        <style>
        .stRadio > label {
            font-size: 18px; /* Increase font size of the label */
        }
        .stRadio div {
            gap: 10px; /* Increase spacing between radio options */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    page_names_to_funcs = {
        "Main Overview": main_overview,
        "Trends": trends_page,
        "Report Download": report_download_page,
        "Subscribe": subscribe_page,
    }

    query_params = st.query_params
    default_page = query_params.get("page", "Main Overview")
    st.sidebar.image("bandscout_logo.png", width=200)
    selected_page = st.sidebar.radio(
        "",
        list(page_names_to_funcs.keys()),
        index=0,
    )

    st.query_params = {"page": selected_page}

    page_names_to_funcs[selected_page]()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )
    load_dotenv()
    run_dashboard()
