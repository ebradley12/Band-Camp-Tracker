"""Script to make the bar chart of top sales by genre."""
from os import environ
import streamlit as st
import psycopg2
from datetime import datetime
from psycopg2 import extensions
import pandas as pd
import altair as alt

from dotenv import load_dotenv
import logging

# Adjust Streamlit logger to suppress errors or specific logs
logger = logging.getLogger('streamlit')
logger.setLevel(logging.CRITICAL)

# Your app code
st.write("Errors from Streamlit won't appear here.")


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


def fetch_sales_per_hour(connection, target_date) -> pd.DataFrame | None:
    query = """
    SELECT
        DATE_TRUNC('hour', sale_date) AS sale_hour,
        COUNT(sale_id) AS total_sales
    FROM sale
    WHERE sale_date::DATE = %s
    GROUP BY sale_hour
    ORDER BY sale_hour;
    """
    sale_data = pd.read_sql(query, connection, params=[target_date])

    if not sale_data.empty:
        return sale_data
    else:
        return None


def get_sales_data(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the total sales of the top
    5 performing genres as a dataframe.
    """
    query = """
    SELECT
        g.genre_name,
        SUM(s.sale_price) AS total_sales
    FROM
        sale s
    JOIN
        release r ON s.release_id = r.release_id
    JOIN
        release_genre rg ON r.release_id = rg.release_id
    JOIN
        genre g ON rg.genre_id = g.genre_id
    GROUP BY
        g.genre_name
    ORDER BY
        total_sales DESC
    LIMIT 5;
    """

    return pd.read_sql_query(query, connection)


def create_genre_sales_chart(connection: extensions.connection) -> alt.Chart | None:
    """
    Generates a bar chart for genre sales data.
    """

    sales_data = get_sales_data(connection)

    if sales_data.empty:
        st.warning("No data available to display.")
        return None

    sales_data = sales_data.sort_values("total_sales", ascending=False)
    sales_data["rank"] = range(1, len(sales_data) + 1)

    custom_colors = ["#2596be", "#51abcb",
                     "#7cc0d8", "#a8d5e5", "#d3eaf2"]

    chart = (
        alt.Chart(sales_data)
        .mark_bar()
        .encode(
            x=alt.X("genre_name:O", title="Genre",
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("total_sales:Q", title="Total Sales (USD)"),
            color=alt.Color(
                "rank:O",
                scale=alt.Scale(domain=[1, 2, 3, 4, 5], range=custom_colors),
                title="Ranking",
                legend=None
            ),
            tooltip=["genre_name", "total_sales", "rank"]
        )
        .properties(
            title="Top 5 Genres by Total Sales",
            width=600,
            height=400
        )
        .configure_title(
            fontSize=24,
            anchor="start"
        )
    )
    return chart


def plot_sales_per_hour(connection: extensions.connection, start_date: datetime, end_date: datetime) -> alt.Chart | None:
    """
    Plots a line graph of sales per hour for the current day.
    """
    try:
        sales_data = fetch_sales_per_hour(connection, start_date)
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
            tooltip=['sale_hour:T', 'total_sales:Q']
        )
        .properties(
            title=f'Sales Per Hour for {str(start_date)}',
            width=700,
            height=400
        )
    )
    return chart
