import boto3
import psycopg2
from psycopg2 import extensions
from fpdf import FPDF
from os import environ
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import base64
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
    Tries to connect to the RDS database.
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

    except psycopg2.OperationalError:
        logging.warning("The database %s doesn't exist", environ["DB_NAME"])
        return None


def get_cursor(connection: extensions.connection) -> extensions.cursor:
    """
    Retrieves a the cursor for querying
    the database from a connection.
    """
    try:
        return connection.cursor()
    except:
        logging.warning("Unable to retrieve cursor for connection")
        return None


def query_top_genres(cursor, date: str) -> list:
    """
    Query the top genres for a given date.
    """
    cursor.execute("""
        SELECT g.genre_name, SUM(s.sale_price)
        FROM sale AS s
        JOIN release AS r ON s.release_id = r.release_id
        JOIN release_genre AS rg ON r.release_id = rg.release_id
        JOIN genre AS g ON rg.genre_id = g.genre_id
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
    cursor.execute(f"""
        SELECT a.artist_name, SUM(s.sale_price)
        FROM sale AS s
        JOIN release AS r ON s.release_id = r.release_id
        JOIN artist AS a ON r.artist_id = a.artist_id
        WHERE s.sale_date = '{date}'
        GROUP BY a.artist_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """)
    return cursor.fetchall()


def query_top_regions(cursor, date: str) -> list:
    """
    Query the top regions (countries) for a given date.
    """
    cursor.execute(f"""
        SELECT c.country_name, SUM(s.sale_price)
        FROM sale AS s
        JOIN country AS c ON s.country_id = c.country_id
        WHERE s.sale_date = '{date}'
        GROUP BY c.country_name
        ORDER BY SUM(s.sale_price) DESC
        LIMIT 5;
    """)
    return cursor.fetchall()


def query_total_transactions_and_sales(cursor, date: str) -> tuple:
    """
    Query the total transactions and sales for a given date.
    """
    try:
        cursor.execute(f"""
            SELECT COUNT(*), SUM(s.sale_price)
            FROM sale AS s
            WHERE s.sale_date = '{date}';
        """)
        result = cursor.fetchone()
        total_transactions = result[0] if result[0] is not None else 0
        total_sales = result[1] if result[1] is not None else 0.0
        return total_transactions, total_sales
    except Exception as e:
        logging.error("Error querying total transactions and sales: %s", e)
        return 0, 0.0


def query_sales_data() -> dict:
    """
    Query sales data from the RDS database for the previous day.
    """
    try:
        # yesterday = datetime.now() - timedelta(days=1)
        # formatted_date = yesterday.strftime("%Y-%m-%d")
        formatted_date = "2024-12-05"

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


def generate_pdf(data: dict, output_file: str, date: str) -> None:
    """
    Generate a PDF report containing sales data.
    """
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(
            200, 10, txt=f"Daily Sales Report ({date})", ln=True, align='C')
        pdf.ln(10)

        total_sales = data.get('total_sales', 0.0) or 0.0
        total_transactions = data.get('total_transactions', 0) or 0

        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 10, txt=f"""Total Sales: ${
                 total_sales:.2f}""", ln=True)
        pdf.cell(200, 10, txt=f"""Total Transactions: {
                 total_transactions}""", ln=True)
        pdf.cell(200, 10, txt=f"Top Genre: {data['top_genre']}", ln=True)
        pdf.cell(200, 10, txt=f"Top Artist: {data['top_artist']}", ln=True)
        pdf.ln(10)

        for section, content in data.items():
            if isinstance(content, list):
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(200, 10, txt=section.replace(
                    '_', ' ').title(), ln=True)
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
        generate_pdf(sales_data, pdf_file, formatted_date)

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


sales_data = query_sales_data()
print(sales_data)

today = datetime.now()
formatted_date = today.strftime("%Y-%m-%d")

pdf_file = f"./daily_sales_report_{formatted_date}.pdf"
generate_pdf(sales_data, pdf_file, formatted_date)
print(f"PDF generated: {pdf_file}")
