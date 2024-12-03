# 1. Main Page
Purpose:
Showcase the most critical metrics from the last 24 hours.

Content:

Current Top Artist
Current Top Genre
Total Sales
Total Revenue in USD
Top Album (The album with the current highest revenue or sales)
Top Track (The track with the current highest revenue or sales)

Optionally include a small bar chart showing the number of sales for the top 5 genres and top 5 artists over the last 24 hours.

# 2. Trends Page

Purpose:
Explore sales trends over time for genres, artists, and regions.

Content:

Current Top 5 Genres:
Chart: Line chart showing sales over time for the top 5 genres.

Current Top 5 Artists:
Chart: Line chart showing sales over time for the top 5 artists.

Sales by Country:
Chart: Bar chart or heatmap displaying sales distribution across countries.

Filters:
Country Selector: Dropdown to filter by country.
Date Range Selector: Range picker to view trends over a custom period.

# 3. Reports Page

Purpose:
Allow users to view and download detailed reports.

Content:

Filters:
Date Picker: Select a specific date to view the corresponding report.

Reports Viewer:
Display the selected report (Including all data for that date).
Include a download button to fetch the PDF from the S3 bucket.

Workflow:
Query the S3 bucket for the report based on the selected date.
Display a download link for the corresponding PDF.

# 4. Settings Page
Purpose:
Manage subscription and alert preferences.

Content:

Daily PDF Reports Subscription:

Message: "If you would like to subscribe to daily PDF reports, please select the option below and enter your email address."
Input Field: Email address input.
Toggle: Checkbox or toggle to subscribe to the daily report.
Database Action: Update the alerts boolean to True in the subscriber table and insert the email if it's not already present.

Top Artist/Genre Alerts Subscription:

Message: "Subscribe to alerts for changes to the current top artist or genre (including sales information)."
Toggle: Checkbox or toggle for subscribing to alerts.
Database Action: Similar to the daily report subscription, update the alerts field.
