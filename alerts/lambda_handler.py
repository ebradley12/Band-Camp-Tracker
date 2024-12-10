"""
This script is designed to be the entry point for an AWS Lambda function.
The purpose of the Lambda function is to to monitor sales data, detect changes
in top artists and genres, and send alert emails to subscribers using AWS SES.
"""
import logging
from alerts import main


def configure_logging():
    """
    Terminal logs configuration.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def lambda_handler(event, context):
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
    except Exception as e:
        logging.error(f"Error during alerts processing: {e}")
        return {
            "statusCode": 500,
            "body": "An error occurred while processing alerts."
        }
