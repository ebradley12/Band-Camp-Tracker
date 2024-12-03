"""Script for transforming data from the Bandcamp API"""
import logging
import re
from datetime import datetime
import requests
import pandas as pd
from bs4 import BeautifulSoup
from extract import main_extract


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


def convert_from_unix_to_datetime(unix: str) -> datetime:
    """
    Converts a unix timestamp into
    'DD-MM-YYYY' format.
    Returns a "None" string if an error occurs.
    """
    try:
        date = datetime.fromtimestamp(int(unix))
        return date.strftime("%d-%m-%Y")
    except ValueError as e:
        logging.error("Invalid unix timestamp: %s", e)
        return "None"


def convert_date_format(date_str: str) -> str:
    """
    Takes dates in the "DD B YYYY" format and
    converts them to 'DD-MM-YYYY'.
    Returns a "None" string if an error occurs.
    """
    try:
        date = datetime.strptime(date_str, "%d %B %Y")
        return date.strftime("%d-%m-%Y")
    except ValueError as e:
        logging.error("Invalid date format: %s", e)
        return "None"


def convert_to_full_url(url: str) -> str:
    """
    Checks if a url is fully formatted.
    Returns the full url if it is not.
    Returns the given url if it is.
    """
    if url.startswith("http"):
        return url

    return "https:" + url


def validate_album_and_track(item_type: str) -> bool:
    """
    Checks whether given item is an album or a track.
    Returns True if it is, False if it isn't.
    """

    if item_type not in ["a", "t"]:
        return False
    return True


def get_sale_information(sales_dict: dict) -> list[dict]:
    """
    Returns a list of dictionaries containing the
    sales information.
    """
    sales_info = []

    events = sales_dict["feed_data"]["events"]

    for event in events:
        items = event["items"][0]

        if not validate_album_and_track(items["item_type"]):
            continue

        if not items["url"]:
            release_date = "None"
            genres = []

        if not get_release_date_from_url(items["url"]):
            release_date = "None"

        release_date = get_release_date_from_url(items["url"])

        genres = get_genres_from_url(items["url"])

        if not items["album_title"]:
            items["album_title"] = "None"

        sale_date = convert_from_unix_to_datetime(items["utc_date"])

        event_information = {"item_type": items["item_type"],
                             "item_description": items["item_description"],
                             "album_title": items["album_title"],
                             "artist_name": items["artist_name"],
                             "country": items["country"],
                             "amount_paid_usd": items["amount_paid_usd"],
                             "genres": genres,
                             "release_date": release_date,
                             "sale_date": sale_date
                             }

        sales_info.append(event_information)

    return sales_info


def get_genres_from_url(artist_url: str) -> list[str]:
    """
    Gets the lists of genres from a given artist URL.
    Returns an empty list if none can be found or an error occurs.
    """
    try:
        full_url = convert_to_full_url(artist_url)
        response = requests.get(full_url, timeout=1000)

        if response.status_code == 200:
            logging.info("Getting genre tags for %s", full_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            tags = soup.find_all('a', class_='tag')

            if tags:
                genres = [tag.text for tag in tags]
                genres = list(set(genres))
                return genres

            logging.info("No genres listed for %s", full_url)
            return []

        logging.warning("Failed to connect to %s, Status Code: %s",
                        full_url, response.status_code)
        return []

    except requests.exceptions.RequestException as e:
        logging.error("Request failed for %s: %s", artist_url, e)

    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

    return []


def get_release_date_from_url(artist_url: str) -> str:
    """
    Retrieves the release date of a song or album provided in the URL.
    Returns an empty string if it cannot be found or an error occurs.
    """
    try:
        full_url = convert_to_full_url(artist_url)
        response = requests.get(full_url, timeout=1000)

        if response.status_code == 200:
            logging.info("Getting release date for %s", full_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            meta_tag = soup.find('meta', attrs={'name': 'description'})

            if meta_tag:
                description_content = meta_tag.get('content')
                if description_content:
                    date_pattern = r'released\s(\d{1,2}\s[a-zA-Z]+\s\d{4})'
                    match = re.search(date_pattern, description_content)
                    if match:
                        release_date = match.group(1)
                        return convert_date_format(release_date)
                else:
                    logging.info(
                        "No release date found in the meta description for %s", full_url)
        else:
            logging.warning("Failed to connect to %s, Status Code: %s",
                            full_url, response.status_code)

    except requests.exceptions.RequestException as e:
        logging.error("Request failed for %s: %s", artist_url, e)

    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

    return ""


def create_sales_dataframe(sales_info: list[dict]) -> pd.DataFrame:
    """
    Inserts given sales data into a dataframe and returns it.
    Also exports it as a .csv file.
    """
    sales_df = pd.json_normalize(sales_info)

    if "sale_date" in sales_df.columns:
        sales_df["sale_date"] = pd.to_datetime(
            sales_df["sale_date"], errors="coerce")

        if sales_df["sale_date"].isna().any():
            logging.warning(
                "Some 'sale_date' entries could not be converted to datetime.")

    sales_df["sale_year"] = sales_df["sale_date"].dt.year
    sales_df["sale_month"] = sales_df["sale_date"].dt.month
    sales_df.to_csv("MUSIC_DATA.csv", index=False)

    return sales_df


def main_transform(sales_data: dict) -> pd.DataFrame:
    """
    Fully transforms given sales data into a dataframe
    and returns it. Also outputs it as a .csv file.
    """
    config_log()
    sale_info = get_sale_information(sales_data)
    return create_sales_dataframe(sale_info)


if __name__ == "__main__":
    sales_data = main_extract()
    main_transform(sales_data)
