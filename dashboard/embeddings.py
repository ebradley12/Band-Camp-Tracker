"""This is the script to create embeddings from currently sold items."""
import re
import asyncio
import logging
from bs4 import BeautifulSoup, Comment
import aiohttp
import requests
import streamlit as st

ALBUM_ID_PATTERN = re.compile(r"album id (\d+)")
TRACK_ID_PATTERN = re.compile(r"track id (\d+)")
SALES_URL = "https://bandcamp.com/api/salesfeed/1/get_initial"
EMBED_BASE_URL = "https://bandcamp.com/EmbeddedPlayer/"


def config_log() -> None:
    """
    Configure logging for the application.
    """
    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M",
        level=logging.INFO,
    )


async def fetch_html(url: str) -> str | None:
    """
    Fetch HTML content from a given URL using aiohttp.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                logging.warning("Non-200 status code %s for %s",
                                response.status, url)
    except aiohttp.ClientError as e:
        logging.error("Failed to fetch HTML from %s: %s", url, e)
    return None


def extract_id_from_comments(comments: list[str], pattern: re.Pattern) -> str | None:
    """
    Extract ID from HTML comments using the provided regex pattern.
    """
    for comment in comments:
        match = pattern.search(comment)
        if match:
            return match.group(1)
    return None


async def get_id_from_url(artist_url: str) -> str | None:
    """
    Extract the album/track ID from the given artist URL.
    """
    full_url = convert_to_full_url(artist_url)
    html_content = await fetch_html(full_url)

    if not html_content:
        logging.warning("Failed to fetch content from %s", full_url)
        return None

    soup = BeautifulSoup(html_content, "html.parser")
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    album_id = extract_id_from_comments(comments, ALBUM_ID_PATTERN)
    if album_id:
        logging.info("Found album ID: %s", album_id)
        return album_id

    track_id = extract_id_from_comments(comments, TRACK_ID_PATTERN)
    if track_id:
        logging.info("Found track ID: %s", track_id)
        return track_id

    logging.info("No relevant IDs found in comments for %s", full_url)
    return None


def convert_to_full_url(url: str) -> str:
    """
    Convert a relative URL to a full URL if needed.
    """
    if url.startswith("http"):
        return url
    return "https:" + url


def get_sales_information() -> dict:
    """
    Retrieve sales information from the Bandcamp API.
    """
    logging.info("Retrieving Sales Data")
    try:
        response = requests.get(SALES_URL, timeout=10)
        if response.status_code != 200:
            logging.warning(
                "Couldn't retrieve Sales Data. Status Code %s", response.status_code
            )
            return {}
        sales_data = response.json()
        logging.info("Sales Data retrieved.")
        return sales_data
    except requests.exceptions.Timeout:
        logging.warning("Request to retrieve Sales Data timed out.")
        return {}
    except requests.exceptions.RequestException as e:
        logging.error("An error occurred: %s", e)
        return {}


def generate_album_embed(title: str, url: str, album_id: str) -> str:
    """
    Generate embed code for an album.
    """
    return (
        f"""<iframe style=\"border: 0; width: 100%; height: 120px;\""
        src=\"{EMBED_BASE_URL}album={album_id}/size=large/bgcol=ffffff/linkcol=0687f5/
        tracklist=false/artwork=small/transparent=true/\" seamless>"
        <a href=\"{url}\">{title}</a></iframe>"""
    )


def generate_track_embed(title: str, url: str, track_id: str) -> str:
    """
    Generate embed code for a track.
    """
    return (
        f"""<iframe style=\"border: 0; width: 100%; height: 120px;\""
        src=\"{EMBED_BASE_URL}track={track_id}/size=large/bgcol=ffffff/linkcol=0687f5/
        tracklist=false/artwork=small/transparent=true/\" seamless>"
        <a href=\"{url}\">{title}</a></iframe>"""
    )


async def retrieve_embed_list(sales_dict: dict) -> list[str]:
    """
    Retrieve a list of Bandcamp embed codes.
    """
    embeds = []
    events = sales_dict.get("feed_data", {}).get("events", [])

    for event in events:
        for item in event.get("items", []):
            if len(embeds) >= 3:
                break

            item_type = item.get("item_type")
            if item_type not in ["a", "t"]:
                continue

            url = item.get("url")
            if not url:
                continue

            full_url = convert_to_full_url(url)
            item_id = await get_id_from_url(full_url)

            if not item_id:
                continue

            if item_type == "a":
                embed = generate_album_embed(
                    item.get("item_description", ""), full_url, item_id)
                embeds.append(embed)

            elif item_type == "t":
                embed = generate_track_embed(
                    item.get("item_description", ""), full_url, item_id)
                embeds.append(embed)

    return embeds


def get_embed_links() -> list[str]:
    """
    Retrieves embed links for albums/tracks currently sold.
    """
    config_log()
    sales = get_sales_information()
    return asyncio.run(retrieve_embed_list(sales))


def show_embeds() -> None:
    """
    Shows the emebeddings on the Streamlit Dashboard.
    """
    embeds = get_embed_links()
    for embed in embeds:
        st.components.v1.html(embed, height=120)
