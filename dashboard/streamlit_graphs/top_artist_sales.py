"""Script that to make the bar chart of the top 5 artists by units sold."""
from os import environ
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


def get_top_artists_by_units(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the top 5 artists based on the total number of units sold.
    """
    query = """
    SELECT
        a.artist_name,
    COUNT(s.sale_id) AS total_units_sold
    FROM
        artist a
    JOIN
        release r ON a.artist_id = r.artist_id
    JOIN
        sale s ON s.release_id = r.release_id
    WHERE
        a.artist_name != 'Various Artists'
    GROUP BY
        a.artist_name
    ORDER BY
        total_units_sold DESC
    LIMIT 5;
    """

    return pd.read_sql_query(query, connection)


def plot_top_artists_by_units(sales_data: pd.DataFrame) -> alt.Chart:
    """
    Creates a bar chart showing the top 5 artists by total units sold.
    The artist names are colored based on their rank.
    """
    sales_data['rank'] = sales_data['total_units_sold'].rank(
        ascending=False, method='first')

    custom_colors = ["#2596be", "#51abcb",
                     "#7cc0d8", "#a8d5e5", "#d3eaf2"]

    chart = (
        alt.Chart(sales_data)
        .mark_bar()
        .encode(

            x=alt.X('artist_name:N', title='Artist',
                    sort='-y', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('total_units_sold:Q', title='Total Units Sold'),
            color=alt.Color(
                'rank:O',
                scale=alt.Scale(domain=[1, 2, 3, 4, 5], range=custom_colors),
                title="Ranking",
                legend=None
            ),
            tooltip=[
                alt.Tooltip('artist_name:N', title="Artist Name"),
                alt.Tooltip('total_units_sold:Q', title="Units Sold"),
                alt.Tooltip('rank:O', title="Rank")
            ]
        )
        .properties(
            title="Top 5 Artists by Units Sold",
            width=700,
            height=400
        )
    )
    return chart


def visualize_sales_per_artist_over_time(connection: extensions.connection) -> None:
    """
    Fetches and visualizes sales data over time for the top 5 artists.
    """
    sales_data = get_top_artists_by_units(connection)

    if sales_data.empty:
        st.warning("No sales data available.")
        return

    chart = plot_top_artists_by_units(sales_data)
    st.altair_chart(chart, use_container_width=True)
