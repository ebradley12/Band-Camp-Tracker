# Dashboard

This folder contains the script and resources necessary for creating the dashboard for the Band Camp Tracker Project. The dashboard, hosted on Streamlit, features several key sections: a Main Overview, Trends Analysis, Report Download, and a Subscribe section. The Subscriber Page allows users to customize their preferences, including genre interests and notification settings, ensuring they receive updates tailored to their chosen genres.

## Files in This Directory

### File Structure
Below details the file structure of this directory.
```
dashboard/ 
    ├── streamlit_graphs/
    |        ├──release_type_chart.py
    |        ├──sales_by_country.py
    |        ├──sales_over_time.py
    |        ├──top_artist_sales.py
    |        ├──top_genre_sales.py
    ├── dashboard.py
    ├── Dockerfile
    ├── subscribe_page_commands.py
    ├── wireframe-design.png

```
### 1. `streamlit_graphs/`
**Description**: This folder contains Python scripts used to generate interactive data visualisations for the Band Camp Tracker dashboard. 

**Key Features**:
- Built using Streamlit, a Python framework for creating data-driven web applications. 
- Focuses on visualising a specific aspect of the dataset stored in the RDS database, providing users with actionable insights into sales and performance metrics. 
- Serve as modular components that can be integrated into the main Streamlit dashboard. 
- Responsible for querying the database, processing the data, and rendering visually engaging charts or graphs.

### 2. `dashboard.py`
**Description**: Provides a user-friendly interface for interacting with the BandCamp Tracker system, allowing users to view trends, download reports, subscribe for alerts, and customize their preferences.

**Key Features**:
- Provides multiple pages, including Trends, Report Downloads, and a Subscribe Page for managing alerts and preferences.
- Allows users to log in with their email, subscribe to daily reports, and set genre-specific alert preferences.
- Features a sidebar menu for easy navigation between pages.
- Integrates with the backend to handle user data and subscription updates securely.

### 3. `Dockerfile`
**Description**: Defines the environment and steps required to containerize the Streamlit dashboard application.

**Key Features**:
- Utilizes Python 3.10 as the base image for compatibility with the dashboard.
- Installs all required dependencies specified in requirements.txt.
- Adds .env file support by installing python-dotenv.
- Defines the default command to execute the dashboard.py script upon container startup.

