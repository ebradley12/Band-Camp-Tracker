"""Streamlit Dashboard main script."""

import re
import streamlit as st


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
    to daily summary PDF reports and/or alerts about
    trends and genres via email.
    """
    st.title("Subscribe Page")
    st.write("Subscribe to updates and alerts below.")

    # Email input
    email = st.text_input("Enter your email address:")

    # Checkboxes for user subscriptions
    subscribe_daily = st.checkbox("Subscribe to daily reports")
    subscribe_alerts = st.checkbox("Subscribe to alerts")

    # Submit button
    if st.button("Submit"):
        if not email:
            st.error("Please enter a valid email address.")
        elif not is_valid_email(email):
            st.error("Invalid email address, try again!")
        else:
            st.success(f"Thank you for subscribing! Email: {email}")
            st.write("Daily Reports Subscription:",
                     "Yes" if subscribe_daily else "No")
            st.write("Alerts Subscription:",
                     "Yes" if subscribe_alerts else "No")

            print(f"Email: {email}")
            print(f"Daily Reports: {subscribe_daily}")
            print(f"Alerts: {subscribe_alerts}")


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
    run_dashboard()
