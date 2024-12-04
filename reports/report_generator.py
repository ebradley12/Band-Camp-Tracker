import boto3
import psycopg2
from fpdf import FPDF
import os
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import base64
import logging


def config_log() -> None:
    """
    Configure logging for the script.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Create a connection to the database.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT']
        )
        return conn
    except Exception as e:
        logging.error("Failed to connect to the database: %s", e)
        raise


def query_top_genres(cursor, date: str) -> list:
    """
    Query the top genres for a given date.
    """
    cursor.execute("""
        SELECT g.genre_name, SUM(s.sale_price)
        FROM sale s
        JOIN release r ON s.release_id = r.release_id
        JOIN release_genre rg ON r.release_id = rg.release_id
        JOIN genre g ON rg.genre_id = g.genre_id
        WHERE s.sale_date = %s
        GROUP BY g.genre_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """, (date,))
    return cursor.fetchall()


def query_top_artists(cursor, date: str) -> list:
    """
    Query the top artists for a given date.
    """
    cursor.execute("""
        SELECT a.artist_name, SUM(s.sale_price)
        FROM sale s
        JOIN release r ON s.release_id = r.release_id
        JOIN artist a ON r.artist_id = a.artist_id
        WHERE s.sale_date = %s
        GROUP BY a.artist_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """, (date,))
    return cursor.fetchall()


def query_top_regions(cursor, date: str) -> list:
    """
    Query the top regions for a given date.
    """
    cursor.execute("""
        SELECT c.country_name, SUM(s.sale_price)
        FROM sale s
        JOIN customer cu ON s.customer_id = cu.customer_id
        JOIN country c ON cu.country_id = c.country_id
        WHERE s.sale_date = %s
        GROUP BY c.country_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """, (date,))
    return cursor.fetchall()


def query_total_transactions_and_sales(cursor, date: str) -> tuple:
    """
    Query the total transactions and sales for a given date.
    """
    cursor.execute("""
        SELECT COUNT(*), SUM(s.sale_price)
        FROM sale
        WHERE sale_date = %s;
    """, (date,))
    return cursor.fetchone() or (0, 0.0)


def query_sales_data() -> dict:
    """
    Query sales data from the RDS database for the previous day.
    """
    try:
        yesterday = datetime.now() - timedelta(days=1)
        formatted_date = yesterday.strftime("%Y-%m-%d")

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                top_genres = query_top_genres(cursor, formatted_date)
                top_artists = query_top_artists(cursor, formatted_date)
                top_regions = query_top_regions(cursor, formatted_date)
                total_transactions, total_sales = query_total_transactions_and_sales(
                    cursor, formatted_date)

        return {
            "total_transactions": total_transactions,
            "total_sales": total_sales,
            "top_genres": [f"{row[0]}: ${row[1]:.2f}" for row in top_genres],
            "top_artists": [f"{row[0]}: ${row[1]:.2f}" for row in top_artists],
            "top_regions": [f"{row[0]}: ${row[1]:.2f}" for row in top_regions],
            "top_genre": top_genres[0][0] if top_genres else "N/A",
            "top_artist": top_artists[0][0] if top_artists else "N/A"
        }
    except Exception as e:
        logging.error("Error querying sales data: %s", e)
        return {}


def generate_pdf(data: dict, output_file: str) -> None:
    """
    Generate a PDF report containing sales data.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Daily Sales Report", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"""Total Sales: ${
                 data['total_sales']:.2f}""", ln=True)
        pdf.cell(200, 10, txt=f"""Total Transactions: {
                 data['total_transactions']}""", ln=True)
        pdf.cell(200, 10, txt=f"Top Genre: {data['top_genre']}", ln=True)
        pdf.cell(200, 10, txt=f"Top Artist: {data['top_artist']}", ln=True)
        pdf.ln(10)

        for section, content in data.items():
            if isinstance(content, list):
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(200, 10, txt=section, ln=True)
                pdf.set_font("Arial", size=12)
                for line in content:
                    pdf.cell(200, 10, txt=line, ln=True)
                pdf.ln(5)

        pdf.output(output_file)
        logging.info(f"PDF report generated at {output_file}")
    except Exception as e:
        logging.error("Error generating PDF: %s", e)
        raise


def upload_to_s3(file_name: str, bucket_name: str, object_name: str) -> None:
    """
    Upload a file to an S3 bucket.
    """
    try:
        s3 = boto3.client('s3')
        s3.upload_file(file_name, bucket_name, object_name)
        logging.info(f"Uploaded {file_name} to {bucket_name}/{object_name}")
    except ClientError as e:
        logging.error("Failed to upload file to S3: %s", e)
        raise


def send_email_with_attachment(pdf_file: str, recipient_email: str) -> None:
    """
    Send an email with a PDF attachment using AWS SES.
    """
    try:
        ses_client = boto3.client('ses', region_name='us-east-1')
        sender_email = os.environ['SENDER_EMAIL']

        with open(pdf_file, "rb") as file:
            pdf_data = file.read()

        pdf_base64 = base64.b64encode(pdf_data).decode()
        subject = "Daily Sales Report"
        body_text = "Please find attached the daily sales report for Band Camp Tracker."

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
        logging.info(f"Email sent successfully: {response}")
    except ClientError as e:
        logging.error("Failed to send email: %s", e)
        raise


def lambda_handler(event: dict) -> dict:
    """
    AWS Lambda function to generate a PDF report, upload it to S3, and email it.
    """
    try:
        config_log()

        sales_data = query_sales_data()

        yesterday = datetime.now() - timedelta(days=1)
        formatted_date = yesterday.strftime("%Y-%m-%d")

        pdf_file = f"/tmp/daily_sales_report_{formatted_date}.pdf"
        generate_pdf(sales_data, pdf_file)

        s3_bucket = os.environ['S3_BUCKET']
        s3_object = f"reports/daily_sales_report_{formatted_date}.pdf"
        upload_to_s3(pdf_file, s3_bucket, s3_object)

        recipient_email = os.environ['RECIPIENT_EMAIL']
        send_email_with_attachment(pdf_file, recipient_email)

        return {
            "statusCode": 200,
            "body": f"PDF report generated, uploaded to {s3_bucket}/{s3_object}, and emailed to {recipient_email}."
        }
    except Exception as e:
        logging.error("Lambda execution failed: %s", e)
        return {"statusCode": 500, "body": "Internal Server Error"}
