import requests
from bs4 import BeautifulSoup
import logging


def config_log() -> None:
    """Terminal logs configuration"""
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )


def get_sales_information() -> dict:
    logging.info("Retrieving Sales Data")
    sales_url = "https://bandcamp.com/api/salesfeed/1/get_initial"
    response = requests.get(sales_url)
    if response.status_code != 200:
        logging.warning(
            "Couldn't retrieve sales data. Status Code %s".format(response.status_code))
    sales_data = response.json()

    return sales_data


if __name__ == "__main__":
    config_log()
    get_sales_information()
