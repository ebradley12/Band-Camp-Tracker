# Report Generation

This folder contains the script and resources required to generate the daily sales report for the Band Camp Tracker project. The report includes key metrics, graphs, and comparisons with previous days' data, and can be exported as a PDF. Additionally, the script is configured to send the previous day's report via email at 09:00 AM the following day.

## Files in This Directory

### 1. `report_generation.py`
**Description**: Handles the generation of the PDF report.

**Key Features**:
- Queries sales data from the database.
- Generates visualizations (bar charts and line charts) using data from the `graphs.py` script.
- Produces a detailed PDF report containing:
  - Key metrics (sales, transactions, top genres, artists, and regions).
  - Comparisons with the previous day's data.
  - Visual representations of revenue and sales trends.

### 2. `emailer.py`
**Description**: Manages email functionality for sending the report to subscribers.

**Key Features**:
- Retrieves subscriber emails from the database based on preferences (e.g., opted-in for reports).
- Sends the PDF report as an attachment using AWS SES.
- Supports multiple recipients and error handling for email delivery issues.

### 3. `queries.py`
**Description**: Contains SQL query functions to retrieve data from the database.

**Key Features**:
- Queries key metrics, such as:
  - Total sales and transactions.
  - Top genres, artists, and regions.
  - Sales trends over time.
- Retrieves subscriber email data for the emailer script.

### 4. `graphs.py`
**Description**: Generates graphs and visualizations for the report.

**Key Features**:
- Creates bar charts for revenue by genre, artist, and region.
- Produces a line chart for sales trends over time.
- Supports error handling for cases with no data.


### 5. `lambda_handler.py`
**Description**: The entry point for AWS Lambda to automate the report generation process.

**Key Features**:
- Orchestrates the process of:
  - Querying sales data.
  - Generating the PDF report.
  - Uploading the report to S3.
  - Sending the report via email.
- Configured for scheduled triggers (e.g., daily at 09:00 AM).

### 6. `requirements.txt`
**Description**: Contains the Python dependencies required specifically for the report generation functionality.
**Note**: Use this file if you're installing dependencies only for the for the scripts in this folder.

### 7. `test_report_generator.py`
**Description**: Contains tests for report_generator.py to ensure normal, working functionality.

---

## Setting Up

### Prerequisites
- Python 3.8 or higher
- Access to the database (RDS or local setup) with the required schema.
- AWS credentials configured for:
  - Uploading reports to S3
  - Sending emails via AWS SES

### Installing Dependencies

#### For This Folder Only
To install dependencies specific to the report generation functionality:
```bash
pip install -r requirements.txt
```

#### For the Entire Project
If you need to set up dependencies for the entire project:
```bash
pip install -r ../requirements.txt
```

## Running the Script

### Generate the PDF Report:
```bash
python3 report_generator.py
```

### Send the Report via Email:
```bash
python3 emailer.py
```

### Run via Lambda:
The `lambda_handler.py` script can be deployed as an AWS Lambda function and triggered daily.

## Configurations

Ensure the following environment variables are set up:

### Database Credentials:
- `DB_HOST` - The host address of the database.
- `DB_PORT` - The port used to access the database.
- `DB_USER` - The user associated with the database.
- `DB_PASSWORD` -  The password for accessing the database.
- `DB_NAME` - The name of the database being accessed.

### AWS S3:
- `S3_BUCKET` (for uploading reports)

### Email:
- `SENDER_EMAIL`

---

## Features

### Report Generation
**What It Includes:**
- Key metrics such as:
  - Total sales and transactions
  - Top genres, artists and countries 
- Bar charts visualising revenue by genre, artist, and region.
- A line chart for sales trends over time
- Comparison with the previous day's data, including percentage changes.

### Automated Email
**Attachment:**
- The script sends the previous day's report via email at **09:00 AM**.

**Recipients:**
- Subscribers opted in for reports (retrieved from the database).

**Attachment:**
- The PDF report for the previous day is attached to the email.

---

## Output

- A **PDF report** is generated in the specified output directory.
- If configured, the report is:
  - **Uploaded to S3.**
  - **Sent via email** to the designated recipient.
