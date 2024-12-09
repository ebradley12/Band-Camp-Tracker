"""Script to make the bar chart of sales by country."""
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


def get_top_country_sales(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the total sales of the top
    5 countries with the most sales.
    """
    query = """
    SELECT
        c.country_name,
        SUM(s.sale_price) AS total_sales    
    FROM
        sale s
    JOIN
        country c ON s.country_id = c.country_id
    GROUP BY
        c.country_name
    ORDER BY
        total_sales DESC
    LIMIT 5;
    """

    return pd.read_sql_query(query, connection)


def create_country_sales_chart(connection: extensions.connection) -> alt.Chart | None:
    """
    Generates a bar chart for genre sales data.
    """

    sales_data = get_top_country_sales(connection)

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
            x=alt.X("country_name:O", title="Country",
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("total_sales:Q", title="Total Sales (USD)"),
            color=alt.Color(
                "rank:O",
                scale=alt.Scale(domain=[1, 2, 3, 4, 5], range=custom_colors),
                title="Ranking",
                legend=None
            ),
            tooltip=[
                alt.Tooltip("country_name", title="Country"),
                alt.Tooltip("total_sales", title="Total Sales"),
                alt.Tooltip("rank", title="Rank")
            ]
        )
        .properties(
            title="Top 5 Countries by Total Sales (USD)",
            width=600,
            height=400
        )
        .configure_title(
            fontSize=24,
            anchor="start"
        )
    )
    return chart


def visualize_country_sales(connection: extensions.connection) -> None:
    """
    Produces the visualization of the sales 
    of the top 5 genres for the Streamlit Dashboard.
    """
    genre_sales = create_country_sales_chart(connection)
    if not genre_sales:
        st.warning("No data available to show.")
    else:
        st.altair_chart(genre_sales, use_container_width=True)
