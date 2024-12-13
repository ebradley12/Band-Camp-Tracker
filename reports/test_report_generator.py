"""This is the script for tests for report generation"""
from unittest.mock import patch, Mock
from io import BytesIO
import logging
from report_generator import (
    add_table_to_pdf,
    generate_summary_section,
    generate_comparison_section,
    add_top_genres_graph,
    generate_daily_report,
    config_log
)


def test_add_table_to_pdf():
    """
    Tests if tables are successfully added to the PDF.
    """
    mock_pdf = Mock()
    headers = ["Metric", "Value"]
    data = [["Total Sales", "$1000"], ["Total Transactions", "200"]]
    column_widths = [50, 50]

    add_table_to_pdf(mock_pdf, headers, data, column_widths)

    assert mock_pdf.cell.call_count == len(headers) + len(data) * len(data[0])
    mock_pdf.ln.assert_called()


def test_generate_summary_section():
    """
    Tests the generation of the summary.
    """
    mock_pdf = Mock()
    current_data = {
        "total_sales": 1000.00,
        "total_transactions": 200,
        "top_genre": ("Rock", 500),
        "top_artist": ("Artist A", 300),
        "top_album": ("Album A", 200),
        "top_track": ("Track A", 100),
    }

    generate_summary_section(mock_pdf, current_data)

    assert mock_pdf.cell.call_count > 0
    mock_pdf.cell.assert_any_call(
        200, 10, txt="Total Sales: $1000.00", ln=True)


def test_generate_comparison_section():
    """
    Tests that the comparisons are working properly.
    """
    mock_pdf = Mock()
    current_data = {"total_sales": 1000, "total_transactions": 200}
    previous_data = {"total_sales": 800, "total_transactions": 150}
    date = "2024-12-11"

    generate_comparison_section(mock_pdf, current_data, previous_data, date)

    assert mock_pdf.cell.call_count > 0
    mock_pdf.cell.assert_any_call(50, 8, "Total Sales", border=1, align="C")


@patch("report_generator.generate_bar_chart")
def test_add_top_genres_graph(mock_generate_bar_chart):
    """
    Tests the additions of genres to the graph.
    """
    mock_pdf = Mock()
    mock_buffer = BytesIO(b"fake-image-data")
    mock_generate_bar_chart.return_value = mock_buffer

    current_data = {"top_genres": [("Rock", 500), ("Pop", 300)]}

    add_top_genres_graph(mock_pdf, current_data)

    mock_generate_bar_chart.assert_called_once()
    mock_pdf.image.assert_called_once()


@patch("report_generator.query_sales_data")
@patch("report_generator.format_pdf")
def test_generate_daily_report(mock_format_pdf, mock_query_sales_data):
    """
    Tests the daily report generation.
    """
    mock_query_sales_data.side_effect = [
        {"total_sales": 1000, "total_transactions": 200},
        {"total_sales": 800, "total_transactions": 150},
    ]

    pdf_path = generate_daily_report()

    mock_query_sales_data.assert_called()
    mock_format_pdf.assert_called_once()
    assert pdf_path.startswith("/tmp/daily_sales_report_")


@patch("report_generator.generate_bar_chart", side_effect=ValueError("Invalid data"))
def test_add_top_genres_graph_with_error(mock_generate_bar_chart):
    """
    Test whether errors are caught when adding genres.
    """
    mock_pdf = Mock()
    current_data = {"top_genres": []}

    add_top_genres_graph(mock_pdf, current_data)

    mock_pdf.cell.assert_called_with(
        200, 10, txt="No data available for Top Genres.", ln=True, align='L')


def test_logging(caplog):
    """
    Tests whether the logging works.
    """
    with caplog.at_level(logging.INFO):
        config_log()
        logging.info("Test message")

    assert "Test message" in caplog.text
