"""The script fo extracting from the Bandcamp API"""
import logging
import requests


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


def get_sales_information() -> dict:
    """
    Returns a JSON dictionary of sales information 
    from the Bandcamp API.
    """

    logging.info("Retrieving Sales Data")
    sales_url = "https://bandcamp.com/api/salesfeed/1/get_initial"
    response = requests.get(sales_url, timeout=1000)
    if response.status_code != 200:
        logging.warning(
            "Couldn't retrieve Sales Data. Status Code %s", response.status_code)
        return {}
    sales_data = response.json()
    logging.info("Sales Data retrieved.")

    return sales_data


def main_extract() -> dict:
    """
    Main function to extract data from the Bandcamp API. 
    Returns a dictionary containing raw data from the API."
    """
    config_log()

    return get_sales_information()


if __name__ == "__main__":
    main_extract()
