FROM public.ecr.aws/lambda/python:3.10

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY emailer.py .
COPY graphs.py .
COPY lambda_handler.py .
COPY queries.py .
COPY report_generator.py .

CMD ["lambda_handler.lambda_handler"]
