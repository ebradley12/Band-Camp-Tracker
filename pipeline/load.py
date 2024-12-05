"""This is the script to load sales data into the database"""
from os import environ
from datetime import datetime
import logging
import ast
import pandas as pd
import psycopg2
from psycopg2 import extensions
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


def validate_env_vars() -> None:
    """
    Raises an error if any environment variables are missing.
    """
    required_vars = ["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME"]
    missing_vars = [var for var in required_vars if var not in environ]
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {missing_vars}")


def get_connection() -> extensions.connection | None:
    """
    Tries to connect to the RDS database.
    """
    try:
        logging.info("Connecting to the database.")
        connection = psycopg2.connect(
            host=environ["DB_HOST"],
            port=environ["DB_PORT"],
            user=environ["DB_USER"],
            password=environ["DB_PASSWORD"],
            database=environ["DB_NAME"]
        )
        logging.info("Connected successfully.")
        return connection
    except psycopg2.OperationalError:
        logging.warning("The database %s doesn't exist", environ["DB_NAME"])
        return None


def get_cursor(connection: extensions.connection) -> extensions.cursor:
    """
    Retrieves the cursor for querying the database from a connection.
    """
    try:
        return connection.cursor()
    except Exception as e:
        logging.error("Unable to retrieve cursor for connection: %s", str(e))
        raise


def get_id_from_table(search_value: str, table_name: str,
                      cursor: extensions.cursor) -> int | None:
    """
    Retrieves the id of a given value from a specified table.
    """
    query = f"""SELECT {table_name}_id FROM {
        table_name} WHERE {table_name}_name = %s;"""
    try:
        cursor.execute(query, (search_value,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logging.error("Error querying %s: %s", table_name, str(e))
        return None


def get_id_from_release_info(release_name: str, release_date: datetime,
                             artist_id: int, type_id: int,
                             cursor: extensions.cursor) -> int | None:
    """
    Retrieves the release id of the
    release with given information.
    """

    check_query = """SELECT release_id FROM release
                    WHERE (release_name = %s
                    AND release_date = %s
                    AND artist_id = %s
                    AND type_id = %s);"""

    cursor.execute(check_query, (release_name,
                                 release_date, artist_id, type_id))
    release_id = cursor.fetchone()

    if release_id:
        return release_id[0]
    return None


def insert_country(country_name: str, cursor: extensions.cursor) -> None:
    """
    Inserts a country into the database if it doesn't already exist.
    """
    try:
        check_query = "SELECT EXISTS (SELECT 1 FROM country WHERE country_name = %s);"
        cursor.execute(check_query, (country_name,))
        exists = cursor.fetchone()[0]

        if not exists:
            insert_query = "INSERT INTO country (country_name) VALUES (%s);"
            cursor.execute(insert_query, (country_name,))
            logging.info(
                "Country '%s' was added to the database.", country_name)

    except psycopg2.Error:
        logging.error("Error inserting country: '%s'", country_name)


def insert_artist(artist_name: str, cursor: extensions.cursor) -> None:
    """
    Inserts an artist into the database if they don't already exist.
    """

    try:
        check_query = """SELECT artist_id FROM artist
                        WHERE artist_name = %s;"""

        cursor.execute(check_query, (artist_name,))
        artist_id = cursor.fetchone()

        if artist_id:
            logging.info(
                "Artist '%s' already exists in with ID: %s.", artist_name, artist_id[0])
        else:
            insert_query = "INSERT INTO artist (artist_name) VALUES (%s);"
            cursor.execute(insert_query, (artist_name,))
            logging.info("Artist '%s' was added to the database.", artist_name)
    except psycopg2.Error:
        logging.error("Error inserting artist: '%s'", artist_name)


def insert_genres(genre_name: str, cursor: extensions.cursor) -> int | None:
    """
    Inserts genres into the database if it doesn't already exist.
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
        return None


def insert_release(release_name: str, release_date: datetime,
                   release_type: str, artist_name: str,
                   cursor: extensions.cursor) -> int | None:
    """
    Inserts a release into the database if it doesn't already exist.
    """
    artist_id = get_id_from_table(artist_name, "artist", cursor)
    type_id = get_id_from_table(release_type, "type", cursor)

    if not artist_id:
        logging.info("Error with provided artist name: %s", artist_name)
        return None

    if not type_id:
        logging.info("Error with provided release_type: %s", release_type)
        return None

    try:
        release_id = get_id_from_release_info(release_name, release_date,
                                              artist_id, type_id, cursor)
        if release_id:
            logging.info(
                "'%s' already exists with release ID %s.", release_name, release_id)
            return release_id

        insert_query = """INSERT INTO release (release_name, release_date, artist_id, type_id)
                            VALUES (%s, %s, %s, %s)
                            RETURNING release_id;"""
        cursor.execute(insert_query, (release_name,
                                      release_date, artist_id, type_id))
        release_id = cursor.fetchone()[0]
        logging.info(
            "Release '%s' of '%s' was added to the database.", release_id, release_name)
        return release_id

    except psycopg2.Error:
        logging.error("Error inserting release: %s", release_name)
        return None


def insert_release_genres(release_id: int, genre_id: int, genre_name: str,
                          release_name: str, cursor: extensions.cursor) -> None:
    """
    Inserts release genres into the database if it doesn't already exist.
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


def insert_sale_data(sale_price: float, sale_date: datetime,
                     country_name: str, release_id: int, cursor) -> None:
    """"
    Inserts the sale data relating to a release into the database.
    """
    country_id = get_id_from_table(country_name, "country", cursor)

    try:
        insert_query = """INSERT INTO sale (sale_price, sale_date, country_id, release_id)
                                VALUES (%s, %s, %s, %s);"""
        cursor.execute(insert_query, (sale_price,
                       sale_date, country_id, release_id))
        logging.info(
            "Purchase of release '%s' added successfully.", release_id)

    except psycopg2.Error:
        logging.error(
            "Error adding purchase of release '%s'", release_id)


def main_load(sales_df: pd.DataFrame) -> None:
    """
    Loads data from the sales dataframe into the database.
    """
    validate_env_vars()
    config_log()
    connection = get_connection()

    if not connection:
        logging.error("Database connection failed. Exiting.")
        return

    cursor = get_cursor(connection)

    if not cursor:
        logging.error("Unable to get cursor. Exiting.")
        return

    try:

        sales_df["genres"] = sales_df["genres"].apply(ast.literal_eval)

        for _, row in sales_df.iterrows():
            insert_country(row["country"], cursor)
            insert_artist(row["artist_name"], cursor)

            release_id = insert_release(row["release_name"], row["release_date"],
                                        row["release_type"], row["artist_name"], cursor)
            if not release_id:
                continue

            for genre in row["genres"]:
                genre_id = insert_genres(genre.title(), cursor)
                if genre_id:
                    insert_release_genres(release_id, genre_id,
                                          genre.title(), row["release_name"], cursor)

            insert_sale_data(row["amount_paid_usd"], row["sale_date"],
                             row["country"], release_id, cursor)

        connection.commit()
        connection.close()

        logging.info("Data loaded successfully.")
    except Exception as e:
        logging.error("Error during data loading: %s", str(e))


if __name__ == "__main__":
    pass
