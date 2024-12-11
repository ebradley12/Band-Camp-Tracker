# **Alerts Folder README**

---

## **Overview**

This folder contains the scripts that control the sending of alerts to subscribers of the bandcamp tracker. The alerts are designed to monitor any changes in the data (top artist, genres) and send an email notification to the user that a change has occurred. 
Aside from the main `alerts.py` script, the folder also contains the dockerfile to create the image, lambda handler which is the entry point for AWS Lambda, `queries.py` which contains all of the SQL queries to obtain the relevant data and finally `utilities.py` which contains supporting functions needed for the alerts.
### Design Philosophy:
1. **Scalability and Performance**: The system is designed to handle a growing number of subscribers and data changes efficiently. By leveraging AWS Lambda for serverless execution, the solution ensures on-demand scalability and minimizes idle resource usage. Optimized SQL queries and streamlined alert logic ensure timely notifications without performance bottlenecks.
2. **Modularity**: The codebase is organized into distinct components each with a clear, single responsibility. This modular design simplifies troubleshooting, promotes code reuse, and makes it easier to extend functionality or integrate additional features in the future.
3. **Reliability and User-centred Focus**: The alert system prioritizes accurate and reliable notifications to subscribers by monitoring data changes with precision. It incorporates error handling and logging to track issues and ensure smooth operation, ultimately focusing on providing a seamless and dependable experience for users.

---

## **Contents**

### **File Structure**
The alerts folder is organised in the following manner:
```
alerts/ 
    ├── alerts.py
    ├── Dockerfile
    ├── lambda_handler.py
    ├── queries.py
    ├── utilities.py
    ├── requirements.txt
```

### **Scripts**
1. **`alerts.py`**
   - The script monitors changes in top artists, genres, and specific subscribed genres on Bandcamp, generating alerts for significant shifts, such as changes in top rankings or spikes in sales, and sends notifications to subscribers via email.
   - It sends personalized email alerts for various scenarios, including a change in the top artist or genre, and sales growth in user-subscribed genres, using SMTP for reliable email delivery.
   - By utilizing SQL queries through a database connection, the script fetches real-time and historical data to calculate metrics like sales deltas and identify changes, ensuring alerts are based on accurate and up-to-date information.
2. **`lambda_handler.py`**
   - This script serves as the entry point for an AWS Lambda function, enabling serverless execution for monitoring sales data and sending email alerts about top artists and genres.
   - It configures logging for detailed runtime insights and includes exception handling to ensure smooth execution and proper reporting of any errors.
   - By invoking the main function from the alerts module, the script efficiently leverages existing alerting logic, making it easy to integrate with AWS Lambda for seamless deployment and scalability.
3. **`queries.py`**
   - This script contains all the functions needed to interact with the database, including retrieving data for top artists, genres, subscriber emails, and sales statistics. These queries power the alert system by fetching the necessary metrics.
   - The script supports dynamic and flexible SQL execution, such as calculating genre sales over specific periods or identifying historic top artists/genres, ensuring precise tracking of trends and changes.
   - Comprehensive error handling and logging ensure that issues in data retrieval are captured and reported, facilitating debugging and maintaining system reliability.
4. **`queries.py`**
   - This script defines key parameters which are critical for controlling the behavior of the alerting system.
   - It includes utility functions for setting up logging, validating environment variables, and converting time intervals into SQL-compatible formats.
5. **`Dockerfile`**
   - The Dockerfile copies the necessary Python scripts into the container’s working directory, preparing them for execution.
   - It installs Python dependencies listed in `requirements.txt` using `pip` with the `--no-cache-dir` flag to minimize image size and optimize build efficiency.
6. **`requirements.txt`**
   - Lists all the Python libraries and their specific versions required by the project, ensuring consistent and predictable behavior across different environments.

---

## **Setting Up**

### **Prerequisites**
- Python 3.8 or higher.
- Access to the database (RDS or local setup) with the required schema.
- AWS credentials configured for:
    - Sending alert emails via AWS SES.

### **Installing Dependencies**
#### **For Alerts Folder Only**
To install dependencies specific to the alerts functionality:
```
pip install -r requirements.txt
```
#### **For Entire Project**
If you are setting up dependencies for the entire project:
```
pip install -r ../requirements.txt
```
## **Running the Script**
### **Run Locally:**
Execute the alert script locally for testing purposes:
```
python3 lambda_handler.py
```
### **Run via Docker:**
To run the alerts application in a containerized environment:

1. Build the Docker image:
```
docker build -t alerts-image .
```
2. Run the container with the required environment variables:
```
docker run --env-file .env alerts-image
```
3. Run via AWS Lambda:
Deploy the `lambda_handler.py` script as an AWS Lambda function to automate alerts.

## **Features**
### **Real-Time Alerts**
What It Does:

1. Monitors the database for:
    - Changes in top artists, genres, or sales trends.
    - Significant growth in genre popularity based on the configured threshold.
    - Sends automated email alerts to subscribers.

2. How It Works:
    - Retrieves subscribed users from the database.
    - Fetches sales and artist performance data.
    - Compares current trends with historical data.
    - Database Queries

3. Key Functions:
    - Identify the top genres and artists over specific time intervals.
    - Determine significant changes in sales trends for genres.
    - Automated Email

4. Recipients:
    - General alerts: All subscribers who opted in for notifications.
    - Genre-specific alerts: Subscribers opted in for specific genres.

5. Content:
    - Includes the latest trends and updates (e.g., "New top artist: Beyoncé").
    - Highlights changes in performance metrics.

6. Output
    - Email Alerts sent to subscribers based on changes in top artists and genres.
    - Logs generated for successful and failed alert operations, useful for debugging.