"""Script for transforming data from the Bandcamp API"""
import logging
import re
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from extract import main_extract


def config_log() -> None:
    """Terminal logs configuration"""
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )


def convert_from_unix_to_datetime(unix: str) -> datetime:
    """Converts a unix timestamp to a regularly
     formatted date"""

    date = datetime.fromtimestamp(unix)

    return date


def convert_to_full_url(url: str) -> str:
    """Checks if a url is valid and returns
    the full url if it is not"""

    if url.startswith("http"):
        return url

    return "https:" + url


def get_sale_information(sales_dict: dict) -> list[dict]:
    """Returns a list of dictionaries containing the
    sales information"""
    sales_info = []

    events = sales_dict["feed_data"]["events"]

    for event in events:
        items = event["items"][0]

        if items["item_type"] not in ["a", "t"]:
            continue

        if items["url"]:
            release_date = get_release_date(items["url"])
            genres = get_genres_from_url(items["url"])
        else:
            release_date = "None"
            genres = []

        sale_date = convert_from_unix_to_datetime(items["utc_date"])

        event_information = {"item_type": items["item_type"],
                             "item_description": items["item_description"],
                             "album_title": items["album_title"],
                             "artist_name": items["artist_name"],
                             "country": items["country"],
                             "amount_paid_usd": items["amount_paid_usd"],
                             "genres": genres,
                             "release_data": release_date,
                             "sale_date": sale_date
                             }

        sales_info.append(event_information)

    return sales_info


def get_genres_from_url(artist_url: str) -> list[str]:
    """Gets the lists of genres from a given artist url.
        Returns an empty list if none can be found."""

    full_url = convert_to_full_url(artist_url)

    response = requests.get(full_url, timeout=1000)

    if response.status_code == 200:
        logging.info("Getting genre tags for %s", full_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        tags = soup.find_all('a', class_='tag')
        if tags:
            genres = [tag.text for tag in tags]
            return genres

        logging.info("No genres listed for %s", full_url)
        return []

    logging.info("Failed to connect to %s, Status Code: %s",
                 full_url, response.status_code)
    return []


def get_release_date(artist_url: str) -> str:
    """Retrieves the release of a song or album
    provided in the url, returns an empty string
    if it cannot be found"""

    full_url = convert_to_full_url(artist_url)

    response = requests.get(full_url, timeout=1000)

    if response.status_code == 200:
        logging.info("Getting release date for for %s", full_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tag = soup.find('meta', attrs={'name': 'description'})

        if meta_tag:
            description_content = meta_tag.get('content')
            if description_content:
                date_pattern = r'released\s(\d{1,2}\s[a-zA-Z]+\s\d{4})'
                match = re.search(date_pattern, description_content)
                if match:
                    release_date = match.group(1)

                    return release_date
            else:
                logging.info("No release date listed for %s", full_url)

    logging.info("Failed to retrieve the webpage: %s", full_url)
    return ""


def create_dataframe(sales_info: list[dict]) -> pd.DataFrame:
    """Returns a dataframe based on received sales information"""
    sales_df = pd.json_normalize(sales_info)

    sales_df.to_csv("MUSIC_DATA.csv")

    return sales_df


if __name__ == "__main__":
    config_log()
    sales_data = main_extract()
    sales_info = get_sale_information(sales_data)
    create_dataframe(sales_info)
