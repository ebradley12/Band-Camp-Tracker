"""Script for transforming data from the Bandcamp API"""
import logging
import re
import asyncio
from datetime import datetime
import geonamescache
import requests
import pandas as pd
import aiohttp
from bs4 import BeautifulSoup
from extract import main_extract


async def fetch_data(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            # Read response text
            if response.headers.get('Content-Type') == 'application/json':
                return await response.json()
            else:
                # Handle non-JSON response
                return await response.text()


def get_locations() -> list:
    """
    Returns a list of countries, country codes, 
    US states and cities.
    Used to filter genres.
    """
    gc = geonamescache.GeonamesCache()

    countries = gc.get_countries()
    states = gc.get_us_states()
    cities = gc.get_cities()

    country_codes = [key.lower() for key in countries.keys()]
    country_names = [country["name"].lower() for country in countries.values()]
    state_names = [state["name"].lower() for state in states.values()]
    city_names = [city["name"].lower() for city in cities.values()]

    all_locations = country_names + state_names + city_names + country_codes

    return all_locations


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


def convert_written_date_format(date_str: str) -> str:
    """
    Takes dates in the "DD B YYYY" format and
    converts them to 'YYYY-MM-DD'.
    Returns a "None" string if an error occurs.
    """
    try:
        date = datetime.strptime(date_str, "%d %B %Y")
        return date.strftime("%Y-%m-%d")
    except ValueError as e:
        logging.error("Invalid date format: %s", e)
        return "None"


def convert_date_format(date_str: str) -> str:
    """
    Converts dates in the 'DD-MM-YYYY' format to 'YYYY-MM-DD'.
    Returns "None" as a string if an error occurs.
    """
    try:
        date = datetime.strptime(date_str, "%d-%m-%Y")
        return date.strftime("%Y-%m-%d")
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

    return item_type in ["a", "t"]


def get_sale_information(sales_dict: dict) -> list[dict]:
    """
    Returns a list of dictionaries containing the
    sales information.
    """
    sales_info = []
    events = sales_dict["feed_data"]["events"]
    locations = get_locations()

    for event in events:
        items = event["items"][0]

        if not validate_album_and_track(items["item_type"]):
            continue

        if not items["url"]:
            release_date = "None"
            genres = []

        release_date = get_release_date_from_url(items["url"])

        if not release_date:
            release_date = "None"

        genres = get_genres_from_url(items["url"], locations)

        if not items["album_title"]:
            items["album_title"] = "None"

        # sale_date = convert_from_unix_to_datetime(items["utc_date"])
        # formatted_sale_date = convert_date_format(sale_date)
        formatted_sale_date = datetime.now()

        event_information = {"release_type": items["item_type"],
                             "release_name": items["item_description"],
                             "album_title": items["album_title"],
                             "artist_name": items["artist_name"],
                             "country": items["country"],
                             "amount_paid_usd": items["amount_paid_usd"],
                             "genres": genres,
                             "release_date": release_date,
                             "sale_date": formatted_sale_date
                             }

        sales_info.append(event_information)

    return sales_info


def get_genres_from_url(artist_url: str, locations: list) -> list[str]:
    """
    Gets the lists of genres from a given artist URL.
    Returns an empty list if none can be found or an error occurs.
    Filters out locations and duplicates automatically.
    """
    try:
        full_url = convert_to_full_url(artist_url)
        response = asyncio.run(fetch_data(full_url))

        if response:
            logging.info("Getting genre tags for %s", full_url)
            soup = BeautifulSoup(response, 'html.parser')
            tags = soup.find_all('a', class_='tag')

            if tags:
                genres = [tag.text for tag in tags if tag.text.lower()
                          not in locations]
                genres = list(set(genres))
                return genres

            logging.info("No genres listed for %s", full_url)
            return []

        logging.warning("GENRES: Failed to connect to %s, Status Code: %s, Message: %s",
                        full_url, response.status_code, response.text)
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
        response = asyncio.run(fetch_data(full_url))

        if response:
            logging.info("Getting release date for %s", full_url)
            soup = BeautifulSoup(response, 'html.parser')
            meta_tag = soup.find('meta', attrs={'name': 'description'})

            if meta_tag:
                description_content = meta_tag.get('content')
                if description_content:
                    date_pattern = r'released\s(\d{1,2}\s[a-zA-Z]+\s\d{4})'
                    match = re.search(date_pattern, description_content)
                    if match:
                        release_date = match.group(1)
                        return convert_written_date_format(release_date)

            logging.info("No valid release date found for %s", full_url)

        else:
            logging.warning("RELEASE DATE: Failed to connect to %s, Status Code: %s",
                            full_url, response.status_code)

    except requests.exceptions.RequestException as e:
        logging.error("Request failed for %s: %s", artist_url, e)

    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

    return ""


def extend_sales_from_df(sales_df: pd.DataFrame) -> None:
    """
    Coverts the "sale_date" column into datetime format 
    and extends the given dataframe with month and year
    of sales.
    Does nothing if a "sale_date" column doesn't exist.
    """

    if "sale_date" in sales_df.columns:
        sales_df["sale_date"] = pd.to_datetime(
            sales_df["sale_date"], errors="coerce")

        if sales_df["sale_date"].isna().any():
            logging.warning(
                "Some 'sale_date' entries could not be converted to datetime.")

    sales_df["sale_year"] = sales_df["sale_date"].dt.year
    sales_df["sale_month"] = sales_df["sale_date"].dt.month


def replace_blank_album_titles(sales_df: pd.DataFrame) -> None:
    """
    Replaces "None" entries in the "album_title" column
    with the name provided in "release_name"
    if the item is an album.
    """

    sales_df.loc[(sales_df["release_type"] == "a") &
                 (sales_df["album_title"].isna() |
                 (sales_df["album_title"] == "None")),
                 "album_title"] = sales_df["release_name"]


def fill_out_album_and_track(sales_df: pd.DataFrame) -> None:
    """
    Replaces the abbreviations for album and track
    with the full "Album" or "Track" in the dataframe.
    Does nothing if a "item_type" column doesn't exist.
    """
    if "release_type" in sales_df.columns:
        sales_df["release_type"] = sales_df["release_type"].map(
            {"a": "album", "t": "track"})


def create_sales_dataframe(sales_info: list[dict]) -> pd.DataFrame:
    """
    Returns the given sales information as a dataframe.
    """
    sales_df = pd.json_normalize(sales_info)

    return sales_df


def clean_sales_dataframe(sales_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and formats the sales dataframe.
    """

    extend_sales_from_df(sales_df)
    replace_blank_album_titles(sales_df)
    fill_out_album_and_track(sales_df)

    sales_df = sales_df[sales_df['release_date'] != "None"]
    sales_df = sales_df[sales_df['sale_date'] != "None"]

    return sales_df


def main_transform(sales_data: dict) -> pd.DataFrame:
    """
    Fully transforms given sales data into a dataframe
    and returns it. 
    """
    config_log()
    sales_info = get_sale_information(sales_data)
    sales_df = create_sales_dataframe(sales_info)
    cleaned_sales_df = clean_sales_dataframe(sales_df)

    return cleaned_sales_df


if __name__ == "__main__":
    pass
