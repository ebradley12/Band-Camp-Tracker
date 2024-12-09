"""
This script handles the generation of the PDF report. It calls SQL query functions from `queries.py`
and visualisation functions from `graphs.py`.
"""

from fpdf import FPDF
from datetime import datetime, timedelta
from queries import query_sales_data
from graphs import generate_bar_chart, generate_sales_over_time_chart
import tempfile
import logging


def config_log() -> None:
    """
    Configure logging for the script.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def add_table_to_pdf(pdf, headers, data, column_widths, row_height=8):
    """
    Add a table to the PDF report.
    """
    pdf.set_font("Arial", 'B', 12)
    for i, header in enumerate(headers):
        pdf.cell(column_widths[i], row_height, header, border=1, align='C')
    pdf.ln(row_height)
    pdf.set_font("Arial", size=10)
    for row in data:
        for i, cell in enumerate(row):
            pdf.cell(column_widths[i], row_height,
                     str(cell), border=1, align='C')
        pdf.ln(row_height)


def generate_summary_section(pdf, current_data):
    """
    Add the summary section to the PDF report.
    """
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Summary", ln=True, align='L')
    pdf.ln(5)

    pdf.set_font("Arial", size=12)
    total_sales = current_data.get('total_sales', 0) or 0
    total_transactions = current_data.get('total_transactions', 0) or 0
    top_genre = current_data.get('top_genre', ("N/A", 0))
    top_artist = current_data.get('top_artist', ("N/A", 0))
    top_album = current_data.get('top_album', ("N/A", 0))
    top_track = current_data.get('top_track', ("N/A", 0))

    pdf.cell(200, 10, txt=f"Total Sales: ${total_sales:.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Total Transactions: {total_transactions}", ln=True)
    pdf.cell(200, 10, txt=f"""Top Genre: {
             top_genre[0]} (${top_genre[1]:.2f})""", ln=True)
    pdf.cell(200, 10, txt=f"""Top Artist: {
             top_artist[0]} (${top_artist[1]:.2f})""", ln=True)
    pdf.cell(200, 10, txt=f"""Top Album: {
             top_album[0]} (${top_album[1]:.2f})""", ln=True)
    pdf.cell(200, 10, txt=f"""Top Track: {
             top_track[0]} (${top_track[1]:.2f})""", ln=True)
    pdf.ln(10)


def generate_comparison_section(pdf, current_data, previous_data, date):
    """
    Add the comparison section to the PDF report.
    """
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Comparison with Previous Day", ln=True, align='L')
    pdf.ln(5)

    total_sales = current_data.get('total_sales', 0) or 0
    total_transactions = current_data.get('total_transactions', 0) or 0
    previous_sales = previous_data.get('total_sales', 0) or 0
    previous_transactions = previous_data.get('total_transactions', 0) or 0

    sales_change = ((total_sales - previous_sales) /
                    previous_sales * 100) if previous_sales else 0
    transactions_change = ((total_transactions - previous_transactions) /
                           previous_transactions * 100) if previous_transactions else 0

    headers = ["Metric", f"{date}", "Previous Day", "Change (%)"]
    comparison_data = [
        ["Total Sales", f"${total_sales:.2f}", f"""${
            previous_sales:.2f}""", f"{sales_change:.1f}%"],
        ["Total Transactions", total_transactions,
            previous_transactions, f"{transactions_change:.1f}%"]
    ]
    add_table_to_pdf(pdf, headers, comparison_data, [50, 40, 50, 40])
    pdf.ln(20)


def add_top_genres_graph(pdf, current_data):
    """
    Add the Top Genres by Revenue graph to the PDF report.
    """
    try:
        buffer = generate_bar_chart(current_data.get(
            "top_genres", []), "Top Genres by Revenue", "Revenue ($)", "")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp_file:
            tmp_file.write(buffer.read())
            pdf.image(tmp_file.name, x=30, y=pdf.get_y(), w=150)
            pdf.ln(20)
    except ValueError as e:
        logging.error(f"Error adding Top Genres graph: {e}")
        pdf.cell(200, 10, txt="No data available for Top Genres.",
                 ln=True, align='L')
        pdf.ln(10)


def add_top_artists_graph(pdf, current_data):
    """
    Add the Top Artists by Revenue graph to the PDF report.
    """
    try:
        buffer = generate_bar_chart(current_data.get(
            "top_artists", []), "Top Artists by Revenue", "Revenue ($)", "")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp_file:
            tmp_file.write(buffer.read())
            pdf.image(tmp_file.name, x=30, y=pdf.get_y(), w=150)
            pdf.ln(20)
    except ValueError as e:
        logging.error(f"Error adding Top Artists graph: {e}")
        pdf.cell(200, 10, txt="No data available for Top Artists.",
                 ln=True, align='L')
        pdf.ln(10)


def add_top_countries_graph(pdf, current_data):
    """
    Add the Top Countries by Revenue graph to the PDF report.
    """
    try:
        buffer = generate_bar_chart(current_data.get(
            "top_regions", []), "Top Countries by Revenue", "Revenue ($)", "")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp_file:
            tmp_file.write(buffer.read())
            pdf.image(tmp_file.name, x=30, y=pdf.get_y(), w=150)
            pdf.ln(20)
    except ValueError as e:
        logging.error(f"Error adding Top Countries graph: {e}")
        pdf.cell(200, 10, txt="No data available for Top Countries.",
                 ln=True, align='L')
        pdf.ln(10)


def add_sales_over_time_graph(pdf, current_data):
    """
    Add the Sales Over Time graph to the PDF report.
    """
    sales_over_time = current_data.get("sales_over_time", [])
    if sales_over_time:
        buffer = generate_sales_over_time_chart(
            sales_over_time, "Sales Over Time")
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp_file:
            tmp_file.write(buffer.read())
            pdf.image(tmp_file.name, x=30, y=pdf.get_y(), w=150)
            pdf.ln(20)
    else:
        pdf.cell(
            200, 10, txt="No sales data available for Sales Over Time.", ln=True, align='L')


def format_pdf(current_data: dict, previous_data: dict, output_file: str, date: str) -> None:
    """
    Format a PDF report containing the daily summary.
    """
    try:
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"""Daily Sales Report ({
                 date})""", ln=True, align='C')
        pdf.ln(10)

        generate_summary_section(pdf, current_data)
        generate_comparison_section(pdf, current_data, previous_data, date)
        add_top_genres_graph(pdf, current_data)
        pdf.add_page()
        pdf.ln(20)
        add_top_artists_graph(pdf, current_data)
        pdf.ln(100)
        add_top_countries_graph(pdf, current_data)
        pdf.add_page()
        add_sales_over_time_graph(pdf, current_data)

        pdf.output(output_file)
        logging.info(f"PDF report generated at {output_file}")

    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error generating PDF: {e}")
        raise RuntimeError(
            "An unexpected error occurred while generating the PDF.") from e


def generate_daily_report():
    """
    Generate the PDF report for the previous day and return the file path.
    """
    try:
        yesterday = datetime.now() - timedelta(days=1)
        day_before_yesterday = yesterday - timedelta(days=1)

        formatted_yesterday = yesterday.strftime("%Y-%m-%d")
        formatted_day_before_yesterday = day_before_yesterday.strftime(
            "%Y-%m-%d")

        current_data = query_sales_data(formatted_yesterday)
        previous_data = query_sales_data(formatted_day_before_yesterday)

        pdf_file = f"/tmp/daily_sales_report_{formatted_yesterday}.pdf"
        format_pdf(current_data, previous_data,
                   pdf_file, formatted_yesterday)

        logging.info(f"PDF report generated: {pdf_file}")
        return pdf_file
    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        raise
    except IOError as io_error:
        logging.error(f"File handling error: {io_error}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error generating daily report: {e}")
        raise RuntimeError(
            "An unexpected error occurred while generating the daily report.") from e


if __name__ == "__main__":
    generate_daily_report()
