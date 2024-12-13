"""Contains various supporting functions used for the alerts."""

import logging
from os import environ


# The period of time between checking for alerts in minutes
ALERT_INTERVAL = 60
# The period of time we use to assess historic trends in minutes
COMPARISON_PERIOD = 2880
# The percentage value a genre has to have grown in popularity before alerting the user
GENRE_NOTIFICATION_THRESHOLD = 1


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


def convert_mins_to_sql_time(minutes: int) -> str:
    """
    Takes a time value in minutes and converts it into a
    string of the time interval it represents backwards from now,
    in a format that an SQL query can understand.
    """
    base_string = "NOW() - INTERVAL "

    if minutes < 1:
        raise ValueError("All config times must be larger than one minute")

    time_string = f"'{minutes} minutes'"

    if minutes == 1:
        time_string = time_string[:-1]

    return base_string + time_string
