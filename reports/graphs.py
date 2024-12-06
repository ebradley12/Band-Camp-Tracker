"""
This script provides functions for generating visualisations as part of the PDF Report.

"""
import matplotlib.pyplot as plt
import io
import logging


def generate_bar_chart(data: list, title: str, xlabel: str, ylabel: str) -> io.BytesIO:
    """
    Generate a bar chart.
    """
    try:
        if not data:
            raise ValueError("No data available for chart generation.")
        labels, values = zip(*data)
        plt.figure(figsize=(10, 6))
        plt.barh(labels, values, color="#2596be")
        plt.title(title, fontsize=16)
        plt.xlabel(xlabel, fontsize=14)
        plt.ylabel(ylabel, fontsize=14)
        plt.tight_layout()
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        plt.close()
        img_buffer.seek(0)
        return img_buffer
    except Exception as e:
        logging.error(f"Error generating bar chart: {e}")
        raise


def generate_sales_over_time_chart(data: list, title: str) -> io.BytesIO:
    """
    Generate a line chart for sales over time.
    """
    plt.figure(figsize=(10, 6))

    if data:
        hours, sales = zip(*data)
        plt.plot(hours, sales, marker="o", linestyle="-",
                 color="#2596be", label="Sales")
        plt.xticks(range(0, 24))
        plt.yticks(range(int(min(sales)) - 10, int(max(sales)) + 20, 10))
    else:
        plt.plot([], [], label="No Data", color="gray")
        plt.xticks(range(0, 24))
        plt.yticks([])

    plt.title(title, fontsize=16)
    plt.xlabel("Hour of Day", fontsize=14)
    plt.ylabel("Total Sales ($)", fontsize=14)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close()
    img_buffer.seek(0)
    return img_buffer
