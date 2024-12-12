"""Script to make the pie chart of album to track releases"""
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


def get_release_type_count(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the count of each type of release; Albums and Tracks
    """
    query = """
    SELECT
        t.type_name,
        COUNT(*) AS total_count    
    FROM
        type t
    JOIN
        release r ON t.type_id = r.type_id
    GROUP BY
        t.type_name;
    """

    return pd.read_sql_query(query, connection)


def create_release_type_pie_chart(connection: psycopg2.connect) -> alt.Chart:
    """
    Creates and returns a pie chart showing the count of 
    each release type (Albums and Tracks).
    """
    release_type_data = get_release_type_count(connection)

    if release_type_data.empty:
        st.warning("No release type data available to display.")
        return None

    chart = (
        alt.Chart(release_type_data)
        .mark_arc()
        .encode(
            theta=alt.Theta(field="total_count",
                            type="quantitative", title="Total Count"),
            color=alt.Color(
                field="type_name",
                type="nominal",
                title="Release Type",
                legend=alt.Legend(title="Release Types"),
                scale=alt.Scale(domain=["album", "track"], range=[
                                "#8c52ff", "#68beec"])
            ),
            tooltip=[
                alt.Tooltip("type_name:N", title="Release Type"),
                alt.Tooltip("total_count:Q", title="Total Releases")
            ]
        )
        .properties(
            title="Distribution of Release Types (Albums vs. Tracks)",
            width=400,
            height=400
        )
    )

    return chart


def visualize_release_types(connection: extensions.connection) -> None:
    """
    Produces the visualization of the pie chart of 
    release types for the Streamlit dashboard.
    """
    genre_sales = create_release_type_pie_chart(connection)
    if not genre_sales:
        st.warning("No data available to show.")
    else:
        st.altair_chart(genre_sales, use_container_width=True)
