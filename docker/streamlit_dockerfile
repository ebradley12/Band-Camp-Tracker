FROM python:3.10

WORKDIR /dashboard

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install python-dotenv

CMD ["python", "dashboard.py"]