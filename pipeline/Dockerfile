FROM public.ecr.aws/lambda/python:3.10

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY extract.py .
COPY transform.py .
COPY load.py .
COPY etl.py .

EXPOSE 80
EXPOSE 443
EXPOSE 5432

CMD [ "etl.lambda_handler" ]
