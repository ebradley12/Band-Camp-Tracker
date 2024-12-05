import boto3
import psycopg2
from psycopg2 import extensions
from fpdf import FPDF
from os import environ
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import base64
import logging
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import pandas as pd
import io
import tempfile

load_dotenv()


def config_log() -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def get_db_connection() -> extensions.connection:
    """Connect to the RDS database."""
    try:
        logging.info("Connecting to the database.")
        connection = psycopg2.connect(
            host=environ["DB_HOST"],
            port=environ["DB_PORT"],
            user=environ["DB_USER"],
            password=environ["DB_PASSWORD"],
            database=environ["DB_NAME"]
        )
        logging.info("Connected successfully.")
        return connection

    except psycopg2.OperationalError:
        logging.warning("Database connection failed.")
        return None


def query_sales_data(date: str) -> dict:
    """Query sales data for a given date."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT g.genre_name, SUM(s.sale_price)
                    FROM sale AS s
                    JOIN release AS r ON s.release_id = r.release_id
                    JOIN release_genre AS rg ON r.release_id = rg.release_id
                    JOIN genre AS g ON rg.genre_id = g.genre_id
                    WHERE s.sale_date = %s
                    GROUP BY g.genre_name
                    ORDER BY SUM(s.sale_price) DESC
                    LIMIT 5;
                """, (date,))
                top_genres = cursor.fetchall()

                cursor.execute("""
                    SELECT a.artist_name, SUM(s.sale_price)
                    FROM sale AS s
                    JOIN release AS r ON s.release_id = r.release_id
                    JOIN artist AS a ON r.artist_id = a.artist_id
                    WHERE s.sale_date = %s
                    GROUP BY a.artist_name
                    ORDER BY SUM(s.sale_price) DESC
                    LIMIT 5;
                """, (date,))
                top_artists = cursor.fetchall()

                cursor.execute("""
                    SELECT c.country_name, SUM(s.sale_price)
                    FROM sale AS s
                    JOIN country AS c ON s.country_id = c.country_id
                    WHERE s.sale_date = %s
                    GROUP BY c.country_name
                    ORDER BY SUM(s.sale_price) DESC
                    LIMIT 5;
                """, (date,))
                top_regions = cursor.fetchall()

                cursor.execute("""
                    SELECT COUNT(*), SUM(s.sale_price)
                    FROM sale AS s
                    WHERE s.sale_date = %s;
                """, (date,))
                total_transactions, total_sales = cursor.fetchone()

                return {
                    "total_transactions": total_transactions,
                    "total_sales": total_sales,
                    "top_genres": [(row[0], row[1]) for row in top_genres],
                    "top_artists": [(row[0], row[1]) for row in top_artists],
                    "top_regions": [(row[0], row[1]) for row in top_regions],
                    "top_genre": top_genres[0][0] if top_genres else "N/A",
                    "top_artist": top_artists[0][0] if top_artists else "N/A"
                }
    except Exception as e:
        logging.error("Error querying sales data: %s", e)
        return {}


def generate_graph(data, title, x_label, y_label, chart_type="bar"):
    """Generates graphs based on the chart type."""
    plt.figure(figsize=(6, 4))
    if chart_type == "bar":
        labels, values = zip(*data) if data else ([], [])
        plt.barh(labels, values, color='skyblue')
    elif chart_type == "line":
        labels, values = zip(*data) if data else ([], [])
        plt.plot(labels, values, marker='o')
    elif chart_type == "line":
        labels, values = zip(*data) if data else ([], [])
        plt.plot(labels, values, marker='o')

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()
    return img_buffer


def generate_pdf(current_data: dict, previous_data: dict, output_file: str, date: str) -> None:
    """
    Generate a detailed PDF report containing the daily summary.
    """
    try:
        pdf = FPDF()
        pdf.add_page()

        # Title and Summary
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"Daily Sales Report ({
                 date})", ln=True, align='C')
        pdf.ln(10)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Total Sales: ${
                 current_data['total_sales'] or 0:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Total Transactions: {
                 current_data['total_transactions'] or 0}", ln=True)
        pdf.cell(200, 10, txt=f"Top Genre: {
                 current_data['top_genre'] or 'N/A'}", ln=True)
        pdf.cell(200, 10, txt=f"Top Artist: {
                 current_data['top_artist'] or 'N/A'}", ln=True)
        pdf.ln(10)

        # Comparison Table
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Comparison with Previous Day", ln=True, align='L')
        pdf.ln(5)

        # Check if there's enough space for the table
        if pdf.get_y() > 240:
            pdf.add_page()

        pdf.set_font("Arial", size=12)
        pdf.cell(60, 10, "Metric", border=1)
        pdf.cell(50, 10, "Today", border=1)
        pdf.cell(50, 10, "Yesterday", border=1)
        pdf.cell(50, 10, "Change (%)", border=1)
        pdf.ln()

        for metric, today_value in [("Total Sales", current_data['total_sales']),
                                    ("Total Transactions", current_data['total_transactions'])]:
            yesterday_value = previous_data.get(metric, 0)
            change_percent = ((today_value - yesterday_value) / yesterday_value * 100
                              if yesterday_value else 0.0)
            pdf.cell(60, 10, metric, border=1)
            pdf.cell(50, 10, f"${today_value:.2f}" if metric ==
                     "Total Sales" else f"{today_value}", border=1)
            pdf.cell(50, 10, f"${yesterday_value:.2f}" if metric ==
                     "Total Sales" else f"{yesterday_value}", border=1)
            pdf.cell(50, 10, f"{change_percent:.1f}%", border=1)
            pdf.ln()
        pdf.ln(10)

        # Helper function to add graphs
        def add_graph_to_pdf(pdf, title, data, chart_type):
            """Helper to add a graph to the PDF and handle page breaks."""
            graph_buffer = generate_graph(
                data, title, "Revenue ($)", "", chart_type=chart_type)
            graph_buffer.seek(0)

            # Save graph to a temporary file for FPDF compatibility
            with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp_file:
                with open(tmp_file.name, "wb") as f:
                    f.write(graph_buffer.read())
                if pdf.get_y() > 240:  # Check if space is running out
                    pdf.add_page()
                pdf.image(tmp_file.name, x=30, y=pdf.get_y(), w=150)
                pdf.ln(70)

        # Top Genres by Revenue (Bar Chart)
        genre_data = [(genre, revenue)
                      for genre, revenue in current_data['top_genres']]
        add_graph_to_pdf(pdf, "Top Genres by Revenue", genre_data, "bar")

        # Top Artists by Revenue (Bar Chart)
        artist_data = [(artist, revenue)
                       for artist, revenue in current_data['top_artists']]
        add_graph_to_pdf(pdf, "Top Artists by Revenue", artist_data, "bar")

        # Top Regions by Revenue (Bar Chart)
        region_data = [(region, revenue)
                       for region, revenue in current_data['top_regions']]
        add_graph_to_pdf(pdf, "Top Regions by Revenue", region_data, "bar")

        # Save the PDF
        pdf.output(output_file)
        logging.info(f"PDF report generated at {output_file}")

    except Exception as e:
        logging.error("Error generating PDF: %s", e)
        raise


# Generate today's and yesterday's data
today = datetime.now()
yesterday = today - timedelta(days=1)

formatted_today = today.strftime("%Y-%m-%d")
formatted_yesterday = yesterday.strftime("%Y-%m-%d")

current_data = query_sales_data(formatted_today)
previous_data = query_sales_data(formatted_yesterday)

# Generate the PDF
pdf_file = f"./daily_sales_report_{formatted_today}.pdf"
generate_pdf(current_data, previous_data, pdf_file, formatted_today)
print(f"PDF generated: {pdf_file}")
