"""The script for extracting from the Bandcamp API."""

import logging
import requests
import aiohttp
import asyncio


def config_log() -> None:
    """
    Terminal logs configuration.
    """
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO
    )


async def fetch_data(url) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


def get_sales_information() -> dict:
    """
    Returns a JSON dictionary of sales information 
    from the Bandcamp API.
    """
    logging.info("Retrieving Sales Data")
    sales_url = "https://bandcamp.com/api/salesfeed/1/get_initial"
    sales_data = asyncio.run(fetch_data(sales_url))
    if sales_data:
        logging.info("Sales Data retrieved.")
        return sales_data

    logging.warning("Could not fetch sales data from API.")
    raise Exception("Error fetching data from API.")


def main_extract() -> dict:
    """
    Main function to extract data from the Bandcamp API. 
    Returns a dictionary containing raw data from the API."
    """
    config_log()

    return get_sales_information()


if __name__ == "__main__":
    main_extract()
