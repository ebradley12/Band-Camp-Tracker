# Report Generation

This folder contains the script and resources required to generate the daily sales report for the Band Camp Tracker project. The report includes key metrics, graphs, and comparisons with previous days' data, and can be exported as a PDF. Additionally, the script is configured to send the previous day's report via email at 09:00 AM the following day.

## Files in This Directory

### 1. `report_generation.py`
- **Description**: The main script responsible for querying the database, generating visualizations, creating the PDF report, and sending the report via email.
- **Key Features**:
  - Queries sales data from the database (genres, artists, regions, transactions, and sales).
  - Produces bar charts for visualizations.
  - Compares current day's data with the previous day's metrics.
  - Outputs a detailed PDF report.
  - Sends the previous day's report via email at 09:00 AM.

### 2. `requirements.txt`
- **Description**: Contains the Python dependencies required specifically for the `report_generation.py` script.
- **Note**: Use this file if you're installing dependencies only for the report generation functionality.

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

### Execute the script to generate the PDF report and send it via email:
```bash
python3 report_generation.py
```

## Configurations

Ensure the following environment variables are set up:

### Database Credentials:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

### AWS S3:
- `S3_BUCKET` (for uploading reports)

### Email:
- `SENDER_EMAIL`
- `RECIPIENT_EMAIL` (for sending reports via SES)

---

## Features

### Report Generation
**What It Includes:**
- Key metrics such as:
  - Total sales
  - Total transactions
  - Top genres
  - Top artists
  - Top regions
- Bar charts visualizing revenue by genre, artist, and region.
- Comparison with the previous day's data, including percentage changes.

### Automated Email
**When It Runs:**
- The script sends the previous day's report via email at **09:00 AM**.

**Recipient:**
- Configured via the `RECIPIENT_EMAIL` environment variable.

**Attachment:**
- The PDF report for the previous day is attached to the email.

---

## Output

- A **PDF report** is generated in the specified output directory.
- If configured, the report is:
  - **Uploaded to S3.**
  - **Sent via email** to the designated recipient.
