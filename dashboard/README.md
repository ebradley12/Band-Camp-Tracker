# Dashboard

This folder contains the script and resources necessary for creating the dashboard for the Band Camp Tracker Project. The dashboard, hosted on Streamlit, features several key sections: a Main Overview, Trends Analysis, Report Download, and a Subscribe section. The Subscriber Page allows users to customise their preferences, including genre interests and notification settings, ensuring they receive updates tailored to their chosen genres.

## Wireframe Design**:  

The layout and functionality of the dashboard are illustrated in the wireframe design:  
![Wireframe Design](./images/wireframe-design.png)


## Files in This Directory

### File Structure
Below details the file structure of this directory.
```
dashboard/ 
    ├── daily_reports/
    ├── streamlit_graphs/
    |        ├──release_type_chart.py
    |        ├──sales_by_country.py
    |        ├──sales_over_time.py
    |        ├──top_artist_sales.py
    |        ├──top_genre_sales.py
    |        ├──queries.py
    ├── dashboard.py
    ├── Dockerfile
    ├── subscribe_page_commands.py
    ├── requirements.txt

```
### 1. `streamlit_graphs/`
**Description**: This folder contains Python scripts used to generate interactive data visualisations for the Band Camp Tracker dashboard. 

**Key Features**:
- Built using Streamlit, a Python framework for creating data-driven web applications. 
- Focuses on visualising a specific aspect of the dataset stored in the RDS database, providing users with actionable insights into sales and performance metrics. 
- Serve as modular components that can be integrated into the main Streamlit dashboard. 
- Responsible for querying the database, processing the data, and rendering visually engaging charts or graphs.
#### `queries.py`
- Provides various SQL queries to retrieve data for visualising key sales metrics, including top artists, tracks, albums, and genres by sales for the current date or specific date ranges.
- Several functions allow querying sales data based on a specific date or a date range, enabling flexible analysis of sales trends over time.
- Aggregates sales data by genre, artist, track, country, and release type, and outputs the results in the form of pandas DataFrames, making it easy to generate visual reports and insights for the dashboard.

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
- Utilises Python 3.10 as the base image for compatibility with the dashboard.
- Installs all required dependencies specified in requirements.txt.
- Adds .env file support by installing python-dotenv.
- Defines the default command to execute the dashboard.py script upon container startup.

### 4. `subscribe_page_commands.py`
**Description**: Contains database operations and commands for managing subscriber data in the Band Camp Tracker application.

**Key Features**:
- Establishes secure connections to the RDS PostgreSQL database using environment variables.
- Provides functionality to add new subscribers and update existing preferences, including genre-specific alerts.
- Supports user unsubscription by removing their data from the database.
- Retrieves and converts genre data for user preferences to ensure seamless user interaction with the dashboard.

### 5. `wireframe-design.png`
**Description**: A visual representation outlining the layout and structure of the Band Camp Tracker dashboard, illustrating key components and navigation flow.

### 6. `requirements.txt`
**Description**: Contains the Python dependencies required specifically for the dashboard generation functionality.
**Note**: Use this file if you're installing dependencies only for the for the scripts in this folder.

---

## Key Features
The dashboard provides a visually engaging interface, with interactive charts and graphs that display key trends and performance metrics. Users can easily navigate through different pages, such as the main overview, trends, and report downloads, via a sidebar. The subscription page allows users to manage their preferences with checkboxes and dropdown menus for alerts and reports, offering a personalised experience. The design is responsive, ensuring optimal display across different devices, making it user-friendly and accessible.

### Main Overview Page
The Main Overview page of the dashboard offers a snapshot of the latest activities within the BandCamp Tracker project. It features a display of the Top Artists, Top Tracks, and other key metrics of the day, giving users quick insights into current trends and popular content. 
Additionally, the page includes music embeds for tracks that were recently purchased, allowing users to directly listen to, and follow a link to purchase, the tracks within the dashboard. 
### Trends Page
The Trends Page of the dashboard is dedicated to visualising key metrics through interactive graphs. It showcases a series of Streamlit-generated graphs that provide insights into various performance indicators, such as sales by country, sales over time, and top genre sales. Users can explore these visualisations to identify trends, patterns, and shifts in the data, helping them to understand the broader landscape of sales activity. Each graph is designed to be intuitive and easy to interpret, offering a clear view of how different factors, like artist performance or genre popularity, are evolving over time.
### Report Download Page
The Report Download Page provides users with the ability to easily access and download historical reports. It features a date range selector, allowing users to choose specific dates or define a range of dates to retrieve the relevant daily summary reports. This functionality gives users the flexibility to find reports from different time periods, making it easier to track and analyze past performance.
### Subscribe Page
The Subscribe Page allows users to manage their subscription preferences. Users can register by entering their email address, and once logged in, they can choose to subscribe to daily reports and alerts for specific genres. The page provides checkboxes for subscribing to general alerts, daily summary reports, and genre-specific notifications. If users opt for genre alerts, they can select their preferred genres from a list. Additionally, users have the option to unsubscribe by clicking a button, which removes their email from the subscription list.

---

## Setting Up

### Prerequisites
- Python 3.8 or higher
- Access to the database (RDS or local setup) with the required schema.

### Installing Dependencies

#### For This Folder Only
To install dependencies specific to the dashboard generation functionality:
```bash
pip install -r requirements.txt
```

#### For the Entire Project
If you need to set up dependencies for the entire project:
```bash
pip install -r ../requirements.txt
```

## Running the Script

### Generate the Dashboard:
```bash
python3 dashboard.py
```

## Configurations

Ensure the following environment variables are set up:

### Database Credentials:
- `DB_HOST` - The host address of the database.
- `DB_PORT` - The port used to access the database.
- `DB_USER` - The user associated with the database.
- `DB_PASSWORD` -  The password for accessing the database.
- `DB_NAME` - The name of the database being accessed.

---
