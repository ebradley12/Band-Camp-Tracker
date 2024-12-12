"""
This script establishes a connection to the database and provides
SQL query functions for retrieving key data needed to generate and email the PDF Report.
"""

import psycopg2
from psycopg2 import extensions
from os import environ
import logging
from dotenv import load_dotenv

load_dotenv()


def config_log() -> None:
    """
    Configure logging for the script.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def get_db_connection() -> extensions.connection:
    """
    Connect to the RDS database.
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

    except ValueError as ve:
        logging.error(f"Environment configuration error: {ve}")
        raise
    except psycopg2.OperationalError:
        logging.warning("The database %s doesn't exist", environ["DB_NAME"])
        return None


def query_data(cursor, query: str, params: tuple) -> list:
    """
    Execute a query and return the results.
    """
    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        logging.error(f"Query failed: {e}")
        return []


def query_top_genres(cursor, date: str) -> list:
    """
    Query the top genres for a given date.
    """
    query = """
        SELECT g.genre_name, SUM(s.sale_price) AS total_revenue
        FROM sale AS s
        JOIN release AS r ON s.release_id = r.release_id
        JOIN release_genre AS rg ON r.release_id = rg.release_id
        JOIN genre AS g ON rg.genre_id = g.genre_id
        WHERE DATE(s.sale_date) = %s
        GROUP BY g.genre_name
        ORDER BY total_revenue DESC
        LIMIT 5;
    """
    return query_data(cursor, query, (date,))


def query_top_artists(cursor, date: str) -> list:
    """
    Query the top artists for a given date.
    """
    query = """
        SELECT a.artist_name, SUM(s.sale_price)
        FROM sale AS s
        JOIN release AS r ON s.release_id = r.release_id
        JOIN artist AS a ON r.artist_id = a.artist_id
        WHERE DATE(s.sale_date) = %s
        AND a.artist_name != 'Various Artists'
        AND a.artist_name != 'Various'
        GROUP BY a.artist_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """
    return query_data(cursor, query, (date,))


def query_top_regions(cursor, date: str) -> list:
    """
    Query the top regions (countries) for a given date.
    """
    query = """
        SELECT c.country_name, SUM(s.sale_price)
        FROM sale AS s
        JOIN country AS c ON s.country_id = c.country_id
        WHERE DATE(s.sale_date) = %s
        GROUP BY c.country_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """
    return query_data(cursor, query, (date,))


def query_top_album(cursor, date: str) -> list:
    """
    Query the top albums for a given date.
    """
    query = """
        SELECT r.release_name, SUM(s.sale_price) AS total_revenue
        FROM sale AS s
        JOIN release AS r ON s.release_id = r.release_id
        WHERE DATE(s.sale_date) = %s
        AND r.type_id = (SELECT type_id FROM type WHERE type_name = 'album')
        GROUP BY r.release_name
        ORDER BY total_revenue DESC
        LIMIT 1;
    """
    return query_data(cursor, query, (date,))


def query_top_track(cursor, date: str) -> list:
    """
    Query the top tracks for a given date.
    """
    query = """
        SELECT r.release_name, SUM(s.sale_price) AS total_revenue
        FROM sale AS s
        JOIN release AS r ON s.release_id = r.release_id
        WHERE DATE(s.sale_date) = %s
        AND r.type_id = (SELECT type_id FROM type WHERE type_name = 'track')
        GROUP BY r.release_name
        ORDER BY total_revenue DESC
        LIMIT 1;
    """
    return query_data(cursor, query, (date,))


def query_total_transactions_and_sales(cursor, date: str) -> tuple:
    """
    Query the total transactions and sales for a given date.
    """
    query = """
        SELECT COUNT(*), SUM(s.sale_price)
        FROM sale AS s
        WHERE DATE(s.sale_date) = %s;
    """
    result = query_data(cursor, query, (date,))
    return result[0] if result else (0, 0)


def query_sales_over_time(cursor, date: str) -> list:
    """
    Query the total sales grouped by hour for a specific day.
    """
    query = """
        SELECT EXTRACT(HOUR FROM s.sale_date) AS hour, SUM(s.sale_price) AS total_sales
        FROM sale AS s
        WHERE DATE(s.sale_date) = %s
        GROUP BY hour
        ORDER BY hour;
    """
    return query_data(cursor, query, (date,))


def query_sales_data(date: str) -> dict:
    """
    Query all sales data from the RDS database for a given date.
    """
    try:
        with get_db_connection() as conn:
            if not conn:
                return {}
            with conn.cursor() as cursor:
                top_genres = query_top_genres(cursor, date)
                top_artists = query_top_artists(cursor, date)
                top_regions = query_top_regions(cursor, date)
                total_transactions, total_sales = query_total_transactions_and_sales(
                    cursor, date)
                sales_over_time = query_sales_over_time(cursor, date)
                top_track_data = query_top_track(cursor, date)
                top_album_data = query_top_album(cursor, date)

        top_genre = (top_genres[0][0], top_genres[0]
                     [1]) if top_genres else ("N/A", 0)
        top_artist = (top_artists[0][0], top_artists[0]
                      [1]) if top_artists else ("N/A", 0)
        top_track = (top_track_data[0][0], top_track_data[0]
                     [1]) if top_track_data else ("N/A", 0)
        top_album = (top_album_data[0][0], top_album_data[0]
                     [1]) if top_album_data else ("N/A", 0)

        return {
            "total_transactions": total_transactions,
            "total_sales": total_sales,
            "top_genres": [(row[0], row[1]) for row in top_genres],
            "top_artists": [(row[0], row[1]) for row in top_artists],
            "top_regions": [(row[0], row[1]) for row in top_regions],
            "sales_over_time": sales_over_time,
            "top_genre": top_genre,
            "top_artist": top_artist,
            "top_track": top_track,
            "top_album": top_album
        }
    except Exception as e:
        logging.error("Error querying sales data: %s", e)
        return {}


def get_report_subscriber_emails(cursor) -> list:
    """
    Retrieve subscriber emails who opted in for PDF reports.
    """
    try:
        query = "SELECT subscriber_email FROM subscriber WHERE subscribe_report = TRUE;"
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error retrieving subscriber emails: {e}")
        raise
