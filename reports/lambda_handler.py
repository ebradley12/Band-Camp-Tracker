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


def lambda_handler(event: dict, context=None) -> dict:
    """
    AWS Lambda function to generate a PDF report, upload it to S3, and email it to subscribers.
    """
    try:
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
        )

        pdf_file = generate_daily_report()

        s3_bucket = environ.get("S3_BUCKET")
        s3_object = f"reports/{pdf_file.split('/')[-1]}"
        upload_to_s3(pdf_file, s3_bucket, s3_object)

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                recipients = get_report_subscriber_emails(cursor)

        if recipients:
            send_email_with_attachment(
                pdf_file=pdf_file,
                recipient_emails=recipients,
                subject="Daily Sales Report",
                body_text="Please find attached the daily sales report."
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
