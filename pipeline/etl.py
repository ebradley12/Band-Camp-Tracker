"""The main ETL pipeline script where we combine Extract, Transform and Load."""

import logging
from extract import main_extract, config_log
from transform import main_transform
from load import main_load


def lambda_handler(event: dict, context=None) -> dict:
    """
    The main pipeline script that fully extract, transforms and loads the Bandcamp data.
    """
    config_log()
    logging.info("\n --- Running The Pipeline --- \n")
    logging.info("\n --- Starting Extract --- \n")
    raw_data = main_extract()
    logging.info("\n --- Extract Complete --- \n")
    logging.info("\n --- Starting Transform --- \n")
    processed_data = main_transform(raw_data)
    logging.info("\n --- Transform Complete --- \n")
    logging.info("\n --- Starting Load --- \n")
    main_load(processed_data)
    logging.info("\n --- Load Complete --- \n")
    logging.info("\n --- Finished Pipeline Execution --- \n")


if __name__ == "__main__":
    lambda_handler(None, None)
