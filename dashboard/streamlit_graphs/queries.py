"""Queries for generating the dashboard visualisations."""
from os import environ
import logging
from datetime import date
import psycopg2
from psycopg2 import extensions
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger('streamlit')
logger.setLevel(logging.ERROR)


load_dotenv()


def get_connection() -> extensions.connection | None:
    """
    Tries to connect to the RDS database.
    """
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
        return None


def get_top_genre(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the top genre by sales for the current date.
    """
    query = """
    SELECT
        g.genre_name,
        SUM(s.sale_price) AS total_sales
    FROM
        sale s
    JOIN
        release r ON s.release_id = r.release_id
    JOIN
        release_genre rg ON r.release_id = rg.release_id
    JOIN
        genre g ON rg.genre_id = g.genre_id
    WHERE
        DATE(s.sale_date) = %(current_date)s
    GROUP BY g.genre_name
    ORDER BY total_sales DESC
    LIMIT 1;
    """
    return pd.read_sql_query(query, connection, params={"current_date": date.today()})


def get_top_track(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the top track by sales for the current date.
    """
    query = """
    SELECT
        r.release_name,
        SUM(s.sale_price) AS total_revenue
    FROM
        sale AS s
    JOIN release AS r ON s.release_id = r.release_id
    JOIN type AS t ON r.type_id = t.type_id
    WHERE
        t.type_name = 'track'
        AND DATE(s.sale_date) = %(current_date)s
    GROUP BY r.release_name
    ORDER BY total_revenue DESC
    LIMIT 1;
    """
    return pd.read_sql_query(query, connection, params={"current_date": date.today()})


def get_top_album(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the top album by sales for the current date.
    """
    query = """
    SELECT
        r.release_name AS album_name,
        SUM(s.sale_price) AS total_sales
    FROM
        sale AS s
    JOIN
        release r ON s.release_id = r.release_id
    WHERE
        r.type_id = (SELECT type_id FROM type WHERE type_name = 'album')
        AND DATE(s.sale_date) = %(current_date)s
    GROUP BY r.release_name
    ORDER BY total_sales DESC
    LIMIT 1;
    """
    return pd.read_sql_query(query, connection, params={"current_date": date.today()})


def get_top_artist(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the top artist by sales for the current date.
    """
    query = """
    SELECT
        a.artist_name,
        SUM(s.sale_price) AS total_sales
    FROM
        sale s
    JOIN
        release r ON s.release_id = r.release_id
    JOIN
        artist a ON r.artist_id = a.artist_id
    WHERE
        a.artist_name != 'Various Artists'
        AND a.artist_name != 'Various'
        AND DATE(s.sale_date) = %(current_date)s
    GROUP BY a.artist_name
    ORDER BY total_sales DESC
    LIMIT 1;
    """
    return pd.read_sql_query(query, connection, params={"current_date": date.today()})


def get_total_sales(connection: extensions.connection) -> float:
    """
    Returns the total sales for the current date.
    """
    query = """
    SELECT
        SUM(s.sale_price) AS total_sales
    FROM
        sale s
    WHERE
        DATE(s.sale_date) = %(current_date)s;
    """
    result = pd.read_sql_query(query, connection, params={
                               "current_date": date.today()})
    return result["total_sales"].iloc[0] if not result.empty else 0.0


def get_top_country(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the top country by sales for the current date.
    """
    query = """
    SELECT
        c.country_name,
        SUM(s.sale_price) AS total_sales
    FROM
        sale s
    JOIN
        country c ON s.country_id = c.country_id
    WHERE
        DATE(s.sale_date) = %(current_date)s
    GROUP BY c.country_name
    ORDER BY total_sales DESC
    LIMIT 1;
    """
    return pd.read_sql_query(query, connection, params={"current_date": date.today()})


def get_release_type_count(connection: extensions.connection) -> pd.DataFrame:
    """
    Returns the count of each type of release; Albums and Tracks
    """
    query = """
    SELECT
        t.type_name,
        COUNT(*) AS total_count    
    FROM
        type t
    JOIN
        release r ON t.type_id = r.type_id
    GROUP BY
        t.type_name;
    """

    return pd.read_sql_query(query, connection)


def get_top_country_sales(connection: extensions.connection, start_date: date, end_date: date = None) -> pd.DataFrame:
    """
    Returns the total sales of the top 5 countries with the most sales for a given date or date range.
    """
    if end_date is None or start_date == end_date:
        query = """
        SELECT
            c.country_name,
            SUM(s.sale_price) AS total_sales    
        FROM
            sale s
        JOIN
            country c ON s.country_id = c.country_id
        WHERE
            s.sale_date = %s
        GROUP BY
            c.country_name
        ORDER BY
            total_sales DESC
        LIMIT 5;
        """
        params = (start_date,)
    else:
        query = """
        SELECT
            c.country_name,
            SUM(s.sale_price) AS total_sales    
        FROM
            sale s
        JOIN
            country c ON s.country_id = c.country_id
        WHERE
            s.sale_date BETWEEN %s AND %s
        GROUP BY
            c.country_name
        ORDER BY
            total_sales DESC
        LIMIT 5;
        """
        params = (start_date, end_date)

    return pd.read_sql_query(query, connection, params=params)


def fetch_sales_within_date_range(connection: psycopg2.connect, start_date: date, end_date: date = None) -> pd.DataFrame:
    """
    Fetches sales data aggregated by hour for a given date range or single date.
    """
    if end_date is None or start_date == end_date:
        query = """
        SELECT
            DATE_TRUNC('hour', sale_date) AS sale_hour,
            COUNT(sale_id) AS total_sales
        FROM sale
        WHERE DATE(sale_date) = %s
        GROUP BY sale_hour
        ORDER BY sale_hour;
        """
        params = (start_date,)
    else:
        query = """
        SELECT
            DATE_TRUNC('hour', sale_date) AS sale_hour,
            COUNT(sale_id) AS total_sales
        FROM sale
        WHERE sale_date BETWEEN %s AND %s
        GROUP BY sale_hour
        ORDER BY sale_hour;
        """
        params = (start_date, end_date)

    try:
        sale_data = pd.read_sql_query(query, connection, params=params)
        if not sale_data.empty:
            return sale_data

        return None
    except Exception as e:
        logging.error("Error fetching sales data: %s", e)
        return None


def get_top_artists_by_units(connection: extensions.connection, start_date: date, end_date: date = None) -> pd.DataFrame:
    """
    Returns the top 5 artists based on the total number of units sold within the given date range.
    """
    if start_date == end_date or end_date is None:
        query = """
        SELECT
            a.artist_name,
            COUNT(s.sale_id) AS total_units_sold
        FROM
            artist a
        JOIN
            release r ON a.artist_id = r.artist_id
        JOIN
            sale s ON s.release_id = r.release_id
        WHERE
            a.artist_name != 'Various Artists'
            AND a.artist_name != 'Various'
            AND s.sale_date = %s
        GROUP BY
            a.artist_name
        ORDER BY
            total_units_sold DESC
        LIMIT 5;
        """
        params = (start_date,)
    else:
        query = """
        SELECT
            a.artist_name,
            COUNT(s.sale_id) AS total_units_sold
        FROM
            artist a
        JOIN
            release r ON a.artist_id = r.artist_id
        JOIN
            sale s ON s.release_id = r.release_id
        WHERE
            a.artist_name != 'Various Artists'
            AND a.artist_name != 'Various'
            AND s.sale_date BETWEEN %s AND %s
        GROUP BY
            a.artist_name
        ORDER BY
            total_units_sold DESC
        LIMIT 5;
        """
        params = (start_date, end_date)

    return pd.read_sql_query(query, connection, params=params)


def get_top_genre_sales(connection: extensions.connection, start_date: date, end_date: date = None) -> pd.DataFrame:
    """
    Returns the total sales of the top 5 performing genres within the given date range or single date.
    """
    if start_date == end_date or end_date is None:
        query = """
        SELECT
            g.genre_name,
            SUM(s.sale_price) AS total_sales
        FROM
            sale s
        JOIN
            release r ON s.release_id = r.release_id
        JOIN
            release_genre rg ON r.release_id = rg.release_id
        JOIN
            genre g ON rg.genre_id = g.genre_id
        WHERE
            s.sale_date = %s
        GROUP BY
            g.genre_name
        ORDER BY
            total_sales DESC
        LIMIT 5;
        """
        params = (start_date,)
    else:
        query = """
        SELECT
            g.genre_name,
            SUM(s.sale_price) AS total_sales
        FROM
            sale s
        JOIN
            release r ON s.release_id = r.release_id
        JOIN
            release_genre rg ON r.release_id = rg.release_id
        JOIN
            genre g ON rg.genre_id = g.genre_id
        WHERE
            s.sale_date BETWEEN %s AND %s
        GROUP BY
            g.genre_name
        ORDER BY
            total_sales DESC
        LIMIT 5;
        """
        params = (start_date, end_date)

    return pd.read_sql_query(query, connection, params=params)
