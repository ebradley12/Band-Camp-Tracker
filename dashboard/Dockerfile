FROM python:3.10-slim

WORKDIR /dashboard

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_graphs ./streamlit_graphs
COPY dashboard.py .
COPY subscribe_page_commands.py .
COPY embeddings.py .
COPY dashboard_formatting.py .
COPY bandscout_logo.png .

RUN mkdir ./daily_reports

EXPOSE 80
EXPOSE 8501
EXPOSE 443

CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]