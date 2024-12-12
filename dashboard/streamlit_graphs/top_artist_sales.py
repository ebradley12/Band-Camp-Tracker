"""Script that to make the bar chart of the top 5 artists by units sold."""
import streamlit as st
from psycopg2 import extensions
import pandas as pd
import altair as alt
from datetime import date, timedelta

from streamlit_graphs.queries import get_top_artists_by_units


def plot_top_artists_by_units(sales_data: pd.DataFrame, start_date: date, end_date: date) -> alt.Chart:
    """
    Creates a bar chart showing the top 5 artists by total units sold.
    The artist names are colored based on their rank.
    """
    sales_data['rank'] = sales_data['total_units_sold'].rank(
        ascending=False, method='first')

    custom_colors = ["#8c52ff", "#8076f9", "#749af2", "#68beec", "#5ce1e6"]

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
            title="Top 5 Artists by Total Sales",
            width=600,
            height=400
        )
        .configure_title(
            fontSize=24,
            anchor="start"
        )
    )
    return chart


def visualise_sales_per_artist_over_time(connection: extensions.connection, start_date: date, end_date: date) -> None:
    """
    Fetches and visualizes sales data over time for the top 5 artists.
    Handles single date or date range selection.
    """
    if start_date > end_date:
        st.error("Start date must be before or equal to the end date.")
        return

    adjusted_end_date = end_date + timedelta(days=1)

    sales_data = get_top_artists_by_units(
        connection, start_date, adjusted_end_date)

    if sales_data.empty:
        st.warning("No sales data available.")
        return

    chart = plot_top_artists_by_units(
        sales_data, start_date, adjusted_end_date)
    st.altair_chart(chart, use_container_width=True)
