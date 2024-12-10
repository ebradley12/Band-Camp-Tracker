FROM public.ecr.aws/lambda/python:3.10

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alerts.py .
COPY queries.py .
COPY lambda_handler.py .
COPY utilities.py .

CMD ["lambda_handler.lambda_handler"]
