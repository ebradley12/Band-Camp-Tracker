"""Script to make the pie chart of album to track releases"""
import streamlit as st
import psycopg2
from psycopg2 import extensions
import altair as alt

from streamlit_graphs.queries import get_release_type_count


def create_release_type_pie_chart(connection: psycopg2.connect) -> alt.Chart:
    """
    Creates and returns a pie chart showing the count of 
    each release type (Albums and Tracks).
    """
    release_type_data = get_release_type_count(
        connection)

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
                legend=alt.Legend(title="Release Types")
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
        .configure_title(
            fontSize=20,
            anchor="start",
            font="Arial"
        )
    )

    return chart


def visualise_release_types(connection: extensions.connection) -> None:
    """
    Produces the visualization of the pie chart of 
    release types for the Streamlit dashboard.
    """
    types = create_release_type_pie_chart(connection)
    if not types:
        st.warning("No data available to show.")
    else:
        st.altair_chart(types, use_container_width=True)
