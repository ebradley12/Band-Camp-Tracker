"""Script to show the line graph of total sales over time."""
from os import environ
from datetime import datetime, timedelta, date
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


def fetch_sales_within_date_range(connection: psycopg2.connect, start_date: date, end_date: date) -> pd.DataFrame | None:
    """
    Fetches sales data aggregated by hour for a given date range.
    """
    if end_date:
        query = """
        SELECT
            DATE_TRUNC('hour', sale_date) AS sale_hour,
            COUNT(sale_id) AS total_sales
        FROM sale
        WHERE sale_date BETWEEN %s AND %s
        GROUP BY sale_hour
        ORDER BY sale_hour;
        """
    else:
        query = """
        SELECT
            DATE_TRUNC('hour', sale_date) AS sale_hour,
            COUNT(sale_id) AS total_sales
        FROM sale
        WHERE DATE(sale_date) = %s
        GROUP BY sale_hour
        ORDER BY sale_hour;
        """
    try:
        date_range = [start_date, end_date]
        if None in date_range:
            date_range.remove(None)
        sale_data = pd.read_sql(query, connection, params=date_range)

        if not sale_data.empty:
            return sale_data

        return None
    except Exception as e:
        logging.error("Error fetching sales data: %s", e)
        return None


def plot_sales_per_hour(connection: psycopg2.connect,
                        start_date: date, end_date=None) -> alt.Chart | None:
    """
    Plots a line graph of sales per hour for the current day.
    """
    try:
        sales_data = fetch_sales_within_date_range(
            connection, start_date, end_date)
        if sales_data.empty:
            st.error("EMPTY - No data available to display")
            return None

    except AttributeError as e:
        st.error("AE - No data available to display")

    if not end_date:
        chart_title = f"Sales on {str(start_date)}"
    else:
        chart_title = f'Sales between {str(start_date)} and {str(end_date - timedelta(days=1))} inclusive'

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
            title=chart_title,
            width=700,
            height=400
        )
    )
    return chart


def visualize_sales_per_hour(connection: psycopg2.connect) -> None:
    """
    Visualizes sales per hour within a date range for the Streamlit dashboard.
    """
    default_end = datetime.now()
    default_start = date(2024, 12, 5)

    date_range = st.date_input(
        "Select a date range:",
        value=(default_start, default_end),  # Default range
        min_value=date(2024, 12, 5),  # Earliest selectable date
        max_value=date.today()       # Latest selectable date
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
        if start_date > end_date:
            st.error("Start date must be before or equal to the end date.")
        else:
            end_date += timedelta(days=1)
            sales_chart = plot_sales_per_hour(connection, start_date, end_date)
            if sales_chart is None:
                st.warning(
                    "No sales data available for the selected date range.")
            else:
                st.altair_chart(sales_chart, use_container_width=True)
    else:
        start_date = date_range[0]
        sales_chart = plot_sales_per_hour(connection, start_date)
        if sales_chart is None:
            st.warning(
                "No sales data available for the selected date range.")
        else:
            st.altair_chart(sales_chart, use_container_width=True)
