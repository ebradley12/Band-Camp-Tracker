"""
This script is designed to be the entry point for an AWS Lambda function.
The purpose of the Lambda function is to generate a daily sales PDF report for the previous day,
upload it to an Amazon S3 bucket, and send the report to subscribers via email using AWS SES.
"""
from os import environ
import logging
import boto3
from botocore.exceptions import ClientError
from report_generator import generate_daily_report
from emailer import send_email_with_attachment
from queries import get_db_connection, get_report_subscriber_emails


def configure_logging():
    """
    Terminal logs configuration.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def lambda_handler(event: dict, context=None) -> dict:
    """
    AWS Lambda function to generate a PDF report, upload it to S3, and email it to subscribers.
    """
    configure_logging()

    sender_email = environ.get("SENDER_EMAIL")
    if not sender_email:
        logging.error("Environment variable SENDER_EMAIL is not set.")
        return {"statusCode": 500, "body": "Internal Server Error: Missing SENDER_EMAIL configuration."}

    try:

        pdf_file = generate_daily_report()
        logging.info("PDF report generated: %s", pdf_file)

        s3_bucket = environ.get("S3_BUCKET")
        s3_object = f"reports/{pdf_file.split('/')[-1]}"
        upload_to_s3(pdf_file, s3_bucket, s3_object)
        logging.info("PDF report uploaded to S3: %s/%s", s3_bucket, s3_object)

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                logging.info(
                    """Fetching report subscriber emails from the database.""")
                recipients = get_report_subscriber_emails(cursor)

        if recipients:
            logging.info("Sending emails to %d recipients.", len(recipients))
            send_email_with_attachment(
                pdf_file=pdf_file,
                recipient_emails=recipients,
                subject="Daily Sales Report",
                body_text="Please find attached the daily sales report.",
                sender_email=sender_email
            )
            logging.info("Emails sent successfully.")
        else:
            logging.info("No subscribers opted in for the PDF report.")

        return {
            "statusCode": 200,
            "body": "Report generated and emailed successfully."
        }
    except ValueError as ve:
        logging.error("Validation error: %s", ve)
        return {"statusCode": 400, "body": "Validation Error: %s" % ve}
    except ClientError as ce:
        logging.error("AWS Client error: %s", ce)
        return {"statusCode": 503, "body": "AWS Service Unavailable. Please try again later."}
    except Exception as e:
        logging.error("Unexpected error: %s", e)
        return {"statusCode": 500, "body": "Internal Server Error. Please check the logs for more details."}


def upload_to_s3(file_name: str, bucket_name: str, object_name: str) -> None:
    """
    Upload a file to an S3 bucket.
    """
    try:
        s3 = boto3.client('s3')
        s3.upload_file(file_name, bucket_name, object_name)
        logging.info("Uploaded %s to %s/%s", file_name,
                     bucket_name, object_name)
    except ClientError as e:
        logging.error("Failed to upload file to S3: %s", e)
        raise
