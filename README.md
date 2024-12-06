# **Band Camp Tracker Project**

---

## **Overview**

The **Band Camp Tracker** is a data-driven project designed to provide insights into trending genres and artists in the music industry. By addressing the challenges of identifying trends in a fragmented and complex market, this project helps uncover what genres are popular and which artists are gaining traction before they become mainstream.

The solution regularly collects and processes sales and genre data from the BandCamp platform, presenting it via a dashboard and automated reports and alerts. 

---

## **Architecture**

The architecture of this project consists of:
1. **Data Extraction**: Using the BandCamp API and web scraping with Beautiful Soup to gather data.
2. **Data Transformation**: Cleaning and standardising the extracted data.
3. **Data Storage**: Storing all data in Amazon RDS for querying and reporting.
4. **Dashboard**: A Streamlit-based dashboard hosted on ECS for real-time data visualisation.
5. **Reports**: Automated daily PDF reports detailing sales trends and performance metrics.
6. **Alerts**: Notifications for key trends triggered by changes in data, implemented via AWS Lambda.
7. **Automation**: EventBridge triggers and Lambda functions to schedule and manage workflows.

Refer to the **[Architecture Diagram](./docs/architecture-diagram.png)** for a detailed view of the system design.

---

## **Features**

### **Dashboard**
The interactive Streamlit dashboard provides:
- **Real-time insights** into sales trends by genre, artist, and region.
- **Dynamic filtering options** for detailed analysis.
- **Visualisations** such as bar charts, line graphs, and heatmaps for intuitive exploration.

The dashboard wireframe provides a visual blueprint of its layout and features.  
Refer to the **[Wireframe Design](./dashboard/wireframe-design.png)** for details.

### **Reports**
Automated daily PDF reports summarising:
- Total sales
- Total transactions
- Top genres, artists, and regions
- A comparison with the previous day's performance

Reports are sent via email with an attachment for the previous day's data at 09:00 AM daily.

### **Alerts**
Automated notifications for:
- Significant increases or decreases in sales by genre or artist.
- Identification of new or emerging trends.

Notifications are triggered by AWS Lambda and sent via email to designated recipients.

---

## **Project Files**

- **ETL Pipelines**:
  - [Pipeline README](./pipeline/README.md)  
    Includes information on the extract, transform, load scripts, and the main ETL pipeline.
  - **Files**:
    - `extract.py`: Data extraction script.
    - `transform.py`: Data transformation script.
    - `load_to_rds.py`: Data loading script.
    - `etl.py`: Main script orchestrating the entire ETL pipeline.
    - `test_etl.py`: Tests for extract, transform and load pipeline script.
    - `requirements.txt`: Python dependencies specific for the pipeline.

- **Streamlit Dashboard**:
  - [Dashboard README](./dashboard/README.md)  
    Documentation for the Streamlit application and its configuration.
  - **Files**:
    - `wireframe-design.png`: Dashboard wireframe design.
    - `app.py`: Streamlit app for visualising data.
    - `requirements.txt`: Python dependencies specific for the dashboard.
  
- **Reports**:
  - [Reports README](./reports/README.md)  
    Documentation for the report generation system.
  - **Files**:
    - `report_generation.py`: Generates daily PDF reports, uploads them to S3, and sends email notifications.
    - `requirements.txt`: Python dependencies specific to the report generation.
  
- **Alerts**:
  - [Reports README](./alerts/README.md)  
    Documentation for the alerts system.
  - **Files**:
    - `alerts.py`: Script for triggering notifications based on key sales trends.
    - `requirements.txt`: Python dependencies specific to alerts.

- **Terraform Infrastructure**:
  - [Terraform README](./infrastructure/README.md)  
    Details the AWS setup scripts for RDS, ECS, EventBridge, and Lambda.
  - **Files**:
    - `main.tf`: Main Terraform configuration file.
    - `variables.tf`: Terraform variables.
    - `outputs.tf`: Terraform outputs.

- **Documentation**:
  - **Files**:
    - `architecture-diagram.png`: Architecture diagram.
    - `erd.png`: Entity Relationship Diagram (ERD).

- **Docker Files**:
  - **Files**:
    - `Dockerfile`: Docker configuration for the ETL pipeline.
    - `docker-compose.yml`: Docker Compose setup for local development.

- **GitHub Workflows**:
  - **Files**:
    - `quality_check.yaml`: Workflow for testing and linting.
    - `deploy.yaml`: Workflow for deployment.

---

## **Planned Outputs**

1. **Dashboard**:
    Real-time visualisation of sales and trends.
    Dynamic filters to explore genres, artists, and countries.

2. **PDF Reports**:
    Automated daily summaries of key metrics.

3. **Alerts**:
    Notifications for current trending genres and artists.

---

## **Setup Instructions**

### **Prerequisites**
- Python 3.11
- Docker
- AWS CLI
- Terraform (for infrastructure setup)

### **Steps**

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/your-org/band-camp-tracker.git
    cd band-camp-tracker
    ```

2. **Install Dependencies**:
  While each directory has its own `requirements.txt` file tailored to its specific functionality, there is also a **main `requirements.txt`** file in the project root.  
  This main file consolidates all dependencies required for the entire project, ensuring consistency across environments and simplifying setup for comprehensive workflows.

    ```bash
    pip install -r requirements.txt
    ```

3. **Set Up Environment Variables**:
   Create a `.env` file in the project root with the following content:
   ```env
   API_KEY=<Your BandCamp API Key>
   DB_USER=<Your RDS Username>
   DB_PASSWORD=<Your RDS Password>
   DB_HOST=<Your RDS Endpoint>
   DB_NAME=<Database Name>
   ```

4. **Run the ETL Pipeline**:
    ```bash
    python3 pipeline/main_pipeline.py
    ```

5. **Generate Reports**:
    ```bash
    python3 reports/report_generation.py
    ```

6. **Set up Alerts**:
    Follow the instructions in the Alerts README.


5. **Deploy Dashboard**: 
    Follow the instructions in the Dashboard README.

---

## **Documentation**

1. **Architecture Diagram**:  
   The high-level system design is visualised below:  
   ![Architecture Diagram](./docs/architecture-diagram.png)

2. **Entity-Relationship Diagram (ERD)**:  
   The database schema and relationships are detailed here:  
   ![Entity-Relationship Diagram](./docs/erd.png)

3. **Wireframe Design**:  
   The layout and functionality of the dashboard are illustrated in the wireframe design:  
   ![Wireframe Design](./dashboard/wireframe-design.png)

---
## **Contributors**

This project was made possible thanks to the collaborative efforts of the following team members:

| Name             | Role             | GitHub Profile                                 |
|------------------|------------------|-----------------------------------------------|
| Ellie Bradley     | Project Manager  | [GitHub](https://github.com/ebradley12)       |
| Emily Curtis      | Architect        | [GitHub](https://github.com/emily-curtis)     |
| Luke Harris       | Architect        | [GitHub](https://github.com/lukieh2014)       |
| Ben Trzcinski     | QA Engineer      | [GitHub](https://github.com/bentrzcinski)     |
| Gabriel Nsiah     | QA Engineer      | [GitHub](https://github.com/GabrielNsiah)     |

---

## Assumptions
- 

---

## Future Improvements
- 