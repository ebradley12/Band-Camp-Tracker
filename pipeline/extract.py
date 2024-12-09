"""The script for extracting from the Bandcamp API"""
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
        level=logging.INFO,
    )


async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # Read response text
            return await response.json()


def get_sales_information() -> dict:
    """
    Returns a JSON dictionary of sales information 
    from the Bandcamp API.
    """
    logging.info("Retrieving Sales Data")
    sales_url = "https://bandcamp.com/api/salesfeed/1/get_initial"

    # try:
    # response = requests.get(sales_url, timeout=1000)
    # if response.status_code != 200:
    #     print(response.text)
    #     logging.warning(
    #         "Couldn't retrieve Sales Data. Status Code %s", response.status_code)
    #     return {}
    # sales_data = response.json()
    # logging.info("Sales Data retrieved.")
    # return sales_data
    sales_data = asyncio.run(fetch_data(sales_url))
    if sales_data:
        logging.info("Sales Data retrieved.")
        return sales_data

    logging.warning("Could not fetch sales data from API.")
    raise Exception("Error fetching data from API.")

    # except requests.exceptions.Timeout:
    #     logging.warning("Request to retrieve Sales Data timed out.")
    #     return {}
    # except requests.exceptions.ConnectionError:
    #     logging.warning("Failed to connect to retrieve Sales Data.")
    #     return {}
    # except requests.exceptions.RequestException as e:
    #     logging.error("An error occurred: %s", e)
    #     return {}


def main_extract() -> dict:
    """
    Main function to extract data from the Bandcamp API. 
    Returns a dictionary containing raw data from the API."
    """
    config_log()

    return get_sales_information()


if __name__ == "__main__":
    main_extract()
