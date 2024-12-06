"""This script extracts subscriber emails from the database and sends the PDF Report via email with AWS SES."""
import boto3
import base64
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from os import environ
from queries import get_subscriber_emails, get_db_connection

load_dotenv()


def config_log() -> None:
    """
    Configure logging for the script.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def send_email_with_attachment(pdf_file: str, recipient_emails: list, subject: str, body_text: str) -> None:
    """
    Send an email with a PDF attachment to multiple recipients using AWS SES.
    """
    try:
        ses_client = boto3.client(
            'ses', region_name=environ.get('AWS_REGION', 'us-east-1'))
        sender_email = environ['SENDER_EMAIL']

        with open(pdf_file, "rb") as file:
            pdf_data = file.read()

        pdf_base64 = base64.b64encode(pdf_data).decode()

        for recipient_email in recipient_emails:
            response = ses_client.send_raw_email(
                RawMessage={
                    'Data': f"From: {sender_email}\n"
                    f"To: {recipient_email}\n"
                    f"Subject: {subject}\n"
                    f"MIME-Version: 1.0\n"
                    f"Content-Type: multipart/mixed; boundary=\"NextPart\"\n\n"
                    f"--NextPart\n"
                    f"Content-Type: text/plain\n\n"
                    f"{body_text}\n\n"
                    f"--NextPart\n"
                    f"Content-Type: application/pdf; name=\"daily_sales_report.pdf\"\n"
                    f"Content-Transfer-Encoding: base64\n"
                    f"Content-Disposition: attachment; filename=\"daily_sales_report.pdf\"\n\n"
                    f"{pdf_base64}\n\n"
                    f"--NextPart--"
                }
            )
            logging.info(f"""Email sent successfully to {
                         recipient_email}: {response}""")
    except ClientError as e:
        logging.error(f"Failed to send email: {e}")
        raise
    except Exception as e:
        logging.error(f"Error sending emails: {e}")
        raise


if __name__ == "__main__":
    """
    Main script to send the daily PDF report to subscribers who opted in for reports.
    """
    try:
        config_log()

        yesterday = datetime.now() - timedelta(days=1)
        formatted_date = yesterday.strftime("%Y-%m-%d")

        pdf_file = f"/tmp/daily_sales_report_{formatted_date}.pdf"

        logging.info("Establishing database connection.")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                logging.info("Retrieving subscriber emails for PDF reports.")
                recipient_emails = get_subscriber_emails(
                    cursor)

        if recipient_emails:
            send_email_with_attachment(
                pdf_file=pdf_file,
                recipient_emails=recipient_emails,
                subject="Daily Sales Report",
                body_text=f"Please find attached the daily sales report for {
                    formatted_date}."
            )
            logging.info("All emails sent successfully.")
        else:
            logging.info("No subscribers opted in for the PDF report.")
    except Exception as e:
        logging.error(f"Failed to send emails: {e}")
