"""This is the script to load plant data into the database"""
from os import environ
from datetime import datetime
import logging
import ast
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()


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


def get_connection() -> psycopg2.extensions.connection:
    """
    Tries to connect to the RDS database.
    Returns a connection if successful.
    """

    logging.info("Connecting to the database.")

    try:
        connection = psycopg2.connect(
            host=environ["DB_HOST"],
            port=environ["DB_PORT"],
            user=environ["DB_USER"],
            password=environ["DB_PASSWORD"],
            database=environ["DB_NAME"]
        )
        return connection
    except psycopg2.OperationalError:
        logging.warning("The database %s doesn't exist", environ["DB_NAME"])
        return None


def get_cursor(connection: psycopg2.extensions.connection) -> psycopg2.extensions.cursor:
    """
    Returns a the cursor for querying
    the database from a connection.
    """
    try:
        return connection.cursor()
    except:
        logging.warning("Unable to retrieve cursor for connection")
        return None


def get_id_from_country(country_name: str, cursor: psycopg2.extensions.cursor) -> int:
    """
    Retrieves the country_id of a 
    given country from the database.
    Returns -1 if it cannot be found.
    """
    search_query = f"SELECT country_id FROM country WHERE country_name = '{
        country_name}';"
    cursor.execute(search_query)
    country_id = cursor.fetchone()
    if not country_id:
        logging.info("Unable to find id for %s", country_name)
        return -1
    return country_id[0]


def get_id_from_artist(artist_name: str, cursor: psycopg2.extensions.cursor) -> int:
    """
    Retrieves the artist id of a 
    given artist from the database.
    Returns -1 if it cannot be found.
    """
    search_query = "SELECT artist_id FROM artist WHERE artist_name = %s;"
    cursor.execute(search_query, (artist_name,))
    artist_id = cursor.fetchone()
    if not artist_id:
        logging.info("Unable to find id for %s", artist_name)
        return -1
    return artist_id[0]


def get_id_from_release_type(release_type: str, cursor: psycopg2.extensions.cursor) -> int:
    """
    Retrieves the release type id of a 
    given release type.
    Returns -1 if it cannot be found.
    """
    search_query = "SELECT type_id FROM type WHERE type_name = %s;"
    cursor.execute(search_query, (release_type.lower(),))
    type_id = cursor.fetchone()
    if not type_id:
        logging.info("Unable to find id for %s", release_type)
        return -1
    return type_id[0]


def insert_country(country_name: str, cursor: psycopg2.extensions.cursor) -> None:
    """
    Inserts a country into the database if it doesn't already exist.
    Logs whether the country was added or already exists.
    """
    try:
        check_query = "SELECT EXISTS (SELECT 1 FROM country WHERE country_name = %s);"
        cursor.execute(check_query, (country_name,))
        exists = cursor.fetchone()[0]

        if exists:
            logging.info(
                "Country '%s' already exists in the database.", country_name)
        else:
            insert_query = "INSERT INTO country (country_name) VALUES (%s);"
            cursor.execute(insert_query, (country_name,))
            logging.info(
                "Country '%s' was added to the database.", country_name)
    except psycopg2.Error:
        logging.error("Error inserting country: '%s'", country_name)


def insert_artist(artist_name: str, country: str, cursor: psycopg2.extensions.cursor) -> None:
    """
    Inserts an artist into the database if they doesn't already exist.
    Logs whether the artist was added or already exists.
    """
    country_id = get_id_from_country(country, cursor)
    try:
        check_query = """SELECT artist_id FROM artist
                        WHERE (artist_name = %s
                        AND country_id = %s);"""
        cursor.execute(check_query, (artist_name, country_id))
        artist_id = cursor.fetchone()

        if artist_id:
            logging.info(
                "Artist '%s' already exists in with ID: %s.", artist_name, artist_id[0])
        else:
            insert_query = "INSERT INTO artist (artist_name, country_id) VALUES (%s, %s);"
            cursor.execute(insert_query, (artist_name, country_id))
            logging.info("Artist '%s' was added to the database.", artist_name)
    except psycopg2.Error:
        logging.error("Error inserting artist: '%s'", artist_name)


def insert_genres(genre_name: str, cursor: psycopg2.extensions.cursor) -> None:
    """
    Inserts genres into the database they don't already exist.
    Logs whether the genre was added or already exists.
    Returns the genre id if inserted/exists.
    Returns -1 in the case of an error.
    """
    try:
        check_query = "SELECT genre_id FROM genre WHERE genre_name = %s LIMIT 1;"
        cursor.execute(check_query, (genre_name,))
        genre_id = cursor.fetchone()

        if genre_id:
            logging.info(
                "Genre '%s' already exists in the database.", genre_name)
            return genre_id[0]

        insert_query = """INSERT INTO genre (genre_name) VALUES (%s)
                            RETURNING genre_id;"""
        cursor.execute(insert_query, (genre_name,))
        logging.info("Genre '%s' was added to the database.", genre_name)
        genre_id = cursor.fetchone()
        return genre_id[0]

    except psycopg2.Error:
        logging.error("Error inserting genre: '%s'", genre_name)
        return -1


def insert_release(release_name: str, release_date: datetime,
                   release_type: str, artist_name: str,
                   cursor: psycopg2.extensions.cursor) -> int:
    """
    Inserts a release into the database if it doesn't already exist.
    Logs whether the release was added or already exists.
    Returns the release id if inserted/exists.
    Returns -1 in the case of an error.
    """
    artist_id = get_id_from_artist(artist_name, cursor)
    type_id = get_id_from_release_type(release_type, cursor)

    if artist_id == -1:
        logging.info("Error with provided artist name: %s", artist_name)
        return -1

    if type_id == -1:
        logging.info("Error with provided release_type: %s", release_type)
        return -1

    try:
        check_query = """SELECT release_id FROM release
                        WHERE (release_name = %s
                        AND release_date = %s
                        AND artist_id = %s
                        AND type_id = %s);"""

        cursor.execute(check_query, (release_name,
                       release_date, artist_id, type_id))
        release_id = cursor.fetchone()

        if release_id:
            logging.info(
                "'%s' already exists with release ID %s.", release_name, release_id[0])
            return release_id[0]

        insert_query = """INSERT INTO release (release_name, release_date, artist_id, type_id)
                            VALUES (%s, %s, %s, %s)
                            RETURNING release_id;"""
        cursor.execute(insert_query, (release_name,
                                      release_date, artist_id, type_id))
        release_id = cursor.fetchone()
        logging.info(
            "Release '%s' of '%s' was added to the database.", release_id, release_name)
        return release_id[0]

    except psycopg2.Error:
        logging.error("Error inserting release: %s", release_name)
        return -1


def insert_release_genres(release_id: int, genre_id: int, genre_name: str,
                          release_name: str, cursor: psycopg2.extensions.cursor) -> None:
    """
    Inserts release genres into the database if it doesn't already exist.
    Logs whether the release genre was added or already exists.
    """
    try:
        check_query = """SELECT EXISTS
                        (SELECT 1 FROM release_genre
                        WHERE release_id = %s
                        AND genre_id = %s);"""

        cursor.execute(check_query, (release_id, genre_id))
        exists = cursor.fetchone()[0]

        if exists:
            logging.info(
                "Release '%s' already has '%s' as a genre.", release_name, genre_name)
        else:
            insert_query = """INSERT INTO release_genre (release_id, genre_id)
                                VALUES (%s, %s);"""
            cursor.execute(insert_query, (release_id, genre_id))
            logging.info(
                "'%s' was added to '%s' successfully.", genre_name, release_name)
    except psycopg2.Error:
        logging.error(
            "Error adding '%s' to '%s' ID: %s", genre_name, release_name, release_id)


def main_load(sales_df: pd.DataFrame) -> None:
    """
    Loads data from the sales dataframe into the database.
    """
    config_log()
    connection = get_connection()
    cursor = get_cursor(connection)

    sales_df["genres"] = sales_df["genres"].apply(ast.literal_eval)

    for _, row in sales_df.iterrows():
        insert_country(row["country"], cursor)
        insert_artist(row["artist_name"], row["country"], cursor)

        release_id = insert_release(row["release_name"], row["release_date"],
                                    row["release_type"], row["artist_name"], cursor)

        for genre in row["genres"]:
            genre_id = insert_genres(genre.lower(), cursor)
            if genre_id == -1:
                continue
            insert_release_genres(release_id, genre_id,
                                  genre.lower(), row["release_name"], cursor)

    connection.commit()


if __name__ == "__main__":
    pass
