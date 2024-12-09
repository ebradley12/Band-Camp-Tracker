"""Script to show the line graph of total sales over time."""
from os import environ
from datetime import datetime
import logging
import streamlit as st
import psycopg2
from psycopg2 import extensions
import pandas as pd
import altair as alt
from dotenv import load_dotenv

logger = logging.getLogger('streamlit')
logger.setLevel(logging.CRITICAL)


load_dotenv()


def get_connection() -> extensions.connection | None:
    """
    Tries to connect to the RDS database.
    """
    try:
        connection = psycopg2.connect(
            host=environ["DB_HOST"],
            port=environ["DB_PORT"],
            user=environ["DB_USER"],
            password=environ["DB_PASSWORD"],
            database=environ["DB_NAME"]
        )
        return connection
    except psycopg2.OperationalError:
        return None


def fetch_sales_within_date_range(connection, start_date, end_date) -> pd.DataFrame | None:
    """
    Fetches sales data aggregated by hour for a given date range.
    """
    query = """
    SELECT
        DATE_TRUNC('hour', sale_date) AS sale_hour,
        COUNT(sale_id) AS total_sales
    FROM sale
    WHERE sale_date BETWEEN %s AND %s
    GROUP BY sale_hour
    ORDER BY sale_hour;
    """
    try:
        sale_data = pd.read_sql(query, connection, params=[
                                start_date, end_date])

        if not sale_data.empty:
            return sale_data

        return None
    except Exception as e:
        logging.error("Error fetching sales data: %s", e)
        return None


def plot_sales_per_hour(connection: extensions.connection,
                        start_date: datetime, end_date: datetime) -> alt.Chart | None:
    """
    Plots a line graph of sales per hour for the current day.
    """
    try:
        sales_data = fetch_sales_within_date_range(
            connection, start_date, end_date)
        if sales_data.empty:
            st.error("No data available to display")
            return None

    except AttributeError as e:
        st.error("No data available to display")

    chart = (
        alt.Chart(sales_data)
        .mark_line(point=True)
        .encode(
            x=alt.X(
                'sale_hour:T',
                title='Hour of the Day',
                axis=alt.Axis(format='%H:%M', titleFontSize=12)
            ),
            y=alt.Y(
                'total_sales:Q',
                title='Total Sales',
                axis=alt.Axis(titleFontSize=12)
            ),
            tooltip=[
                alt.Tooltip('sale_hour:T', title="Date of Sale"),
                alt.Tooltip('total_sales:Q', title="Total Sales")
            ]
        )
        .properties(
            title=f'Sales between {str(start_date)} and {str(end_date)}',
            width=700,
            height=400
        )
    )
    return chart


def visualize_sales_per_hour(connection: extensions.connection) -> None:
    """
    Visualizes sales per hour within a date range for the Streamlit dashboard.
    """
    default_start = datetime(2024, 12, 1)
    default_end = datetime(2024, 12, 6)

    date_range = st.date_input(
        "Select Date Range:",
        value=(default_start.date(), default_end.date())
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        if start_date > end_date:
            st.error("Start date must be before or equal to the end date.")
        else:
            sales_chart = plot_sales_per_hour(connection, start_date, end_date)
            if sales_chart is None:
                st.warning(
                    "No sales data available for the selected date range.")
            else:
                st.altair_chart(sales_chart, use_container_width=True)
    else:
        st.info("Please select a valid date range.")
