# **Pipeline Folder README**

---

## **Overview**

This folder contains the scripts that implement the ETL (Extract, Transform, Load) process for the Band Camp Tracker project. The pipeline extracts raw data from the BandCamp API, processes and enriches it with additional information (e.g., genres), cleans and transforms the data, and finally loads it into an Amazon RDS instance for storage and analysis.

---

## **Contents**

### **Scripts**
1. **`extract.py`**  
   - Extracts raw sales data from the BandCamp API.
   - Retrieves JSON data for further processing.
   - Includes logging and error handling for failed API calls.

2. **`transform.py`**  
   - Transforms the raw data into a structured and cleaned format.
   - Enriches data with genres and release dates scraped from BandCamp URLs.
   - Includes robust error handling and data validation.

3. **`load_to_rds.py`**  
   - Loads the transformed data into the Amazon RDS database.
   - Handles database connections and inserts data into appropriate tables.

4. **`etl.py`**  
   - Orchestrates the entire ETL process by sequentially calling the `extract`, `transform`, and `load` scripts.
   - Provides a modular approach for running the full pipeline or individual components.

5. **`test_etl.py`**  
   - Contains unit tests to validate the functionality of each stage of the ETL pipeline.
   - Tests the following:
     - **Extraction**: Ensures API calls work and handle edge cases like missing or malformed data.
     - **Transformation**: Validates data cleaning, enrichment, and formatting logic.
     - **Loading**: Tests insertion into the database, ensuring no duplicates or constraint violations.
   - Uses mock data and libraries like `pytest` for robust testing.

---

## **How to Run the Pipeline**

### **Prerequisites**
- Python 3.10 or later.
- Required Python libraries installed (listed in `requirements.txt`).
- `.env` file in the root directory containing the necessary environment variables:
  ```env
  API_KEY=<Your BandCamp API Key>
  DB_USER=<Your RDS Username>
  DB_PASSWORD=<Your RDS Password>
  DB_HOST=<Your RDS Endpoint>
  DB_NAME=<Database Name>

# **Run the Pipeline:**
    ```bash
    python3 etl.py
    ```

---

## **Testing**

The test_pipeline.py script provides comprehensive tests for the ETL pipeline. To run the tests:
    ```bash
    pytest test_etl.py
    ```