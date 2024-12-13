# pylint: disable=unused-argument
"""
This script is designed to be the entry point for an AWS Lambda function.
The purpose of the Lambda function is to to monitor sales data, detect changes
in top artists and genres, and send alert emails to subscribers using AWS SES.
"""
import logging
from alerts import main


def configure_logging() -> None:
    """
    Terminal logs configuration.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def lambda_handler(event: dict, context=None) -> dict:
    """
    AWS Lambda handler for sending artist and genre-based alerts.
    """
    configure_logging()
    try:
        main()

        logging.info("Alerts processing completed successfully.")
        return {
            "statusCode": 200,
            "body": "Alerts sent successfully."
        }
    except ValueError as e:
        logging.error("Error during alerts processing: %s", e)
        return {
            "statusCode": 500,
            "body": "An error occurred while processing alerts."
        }
