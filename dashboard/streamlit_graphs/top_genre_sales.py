"""Script to make the bar chart of sales of the top 5 genres."""
from datetime import date, timedelta
import streamlit as st
from psycopg2 import extensions
import altair as alt

from streamlit_graphs.queries import get_top_genre_sales


def create_genre_sales_chart(connection: extensions.connection,
                             start_date: date, end_date: date) -> alt.Chart:
    """
    Generates a bar chart for genre sales data.
    """

    adjusted_end_date = end_date + timedelta(days=1)

    sales_data = get_top_genre_sales(connection, start_date, adjusted_end_date)

    if sales_data.empty:
        st.warning("No data available to display.")
        return None

    sales_data = sales_data.sort_values("total_sales", ascending=False)
    sales_data["rank"] = range(1, len(sales_data) + 1)

    custom_colors = ["#8c52ff", "#8076f9", "#749af2", "#68beec", "#5ce1e6"]

    chart = (
        alt.Chart(sales_data)
        .mark_bar()
        .encode(
            x=alt.X(
                "genre_name:O",
                title="Genre",
                axis=alt.Axis(labelAngle=0),
                sort=alt.EncodingSortField(
                    field="total_sales",
                    order="descending"
                )
            ),
            y=alt.Y("total_sales:Q", title="Total Sales (USD)"),
            color=alt.Color(
                "rank:O",
                scale=alt.Scale(domain=[1, 2, 3, 4, 5], range=custom_colors),
                title="Ranking",
                legend=None
            ),
            tooltip=[
                alt.Tooltip("genre_name", title="Genre"),
                alt.Tooltip("total_sales", title="Total Sales"),
                alt.Tooltip("rank", title="Rank")
            ]
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


def visualise_genre_sales(connection: extensions.connection,
                          start_date: date, end_date: date) -> None:
    """
    Produces the visualization of the sales 
    of the top 5 genres for the Streamlit Dashboard.
    """
    if start_date > end_date:
        st.error("Start date must be before or equal to the end date.")
        return

    adjusted_end_date = end_date + timedelta(days=1)

    genre_sales_chart = create_genre_sales_chart(
        connection, start_date, adjusted_end_date)
    if not genre_sales_chart:
        st.warning("No data available to show.")
    else:
        st.altair_chart(genre_sales_chart, use_container_width=True)
