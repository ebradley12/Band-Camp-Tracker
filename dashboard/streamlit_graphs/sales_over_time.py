"""Script to show the line graph of total sales over time."""
from datetime import datetime, timedelta, date
import streamlit as st
import psycopg2
import altair as alt

from streamlit_graphs.queries import fetch_sales_within_date_range


def plot_sales_per_hour(connection: psycopg2.connect,
                        start_date: date, end_date: date = None) -> alt.Chart | None:
    """
    Plots a line graph of sales per hour for the current day or date range.
    """
    try:
        sales_data = fetch_sales_within_date_range(
            connection, start_date, end_date)
        if sales_data.empty:
            st.error("No data available to display")
            return None

    except AttributeError as e:
        st.error("No data available to display")

    if not end_date:
        chart_title = f"Sales on {str(start_date)}"
    else:
        chart_title = f'Sales between {str(start_date)} and {
            str(end_date - timedelta(days=1))} inclusive'

    chart = (
        alt.Chart(sales_data)
        .mark_line(color="#8c52ff")
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
            title="Total Sales per Hour",
            width=700,
            height=400
        )
        .configure_title(
            fontSize=20,
            anchor="start",
            font="Arial"
        ) + alt.Chart(sales_data)  # Add another chart for points
        .mark_point(color='#4682B4')  # Set the color of the points
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
            ))
    )
    return chart


def visualise_sales_per_hour(connection: psycopg2.connect, start_date: date, end_date: date) -> None:
    """
    Visualises sales per hour within a date range for the Streamlit dashboard.
    """
    if start_date > end_date:
        st.error("Start date must be before or equal to the end date.")
        return

    adjusted_end_date = end_date + timedelta(days=1)
    sales_chart = plot_sales_per_hour(
        connection, start_date, adjusted_end_date)
    if sales_chart is None:
        st.warning(
            "No sales data available for the selected date range.")
    else:
        st.altair_chart(sales_chart, use_container_width=True)
