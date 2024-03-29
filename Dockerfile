FROM python:3.8

RUN pip install poetry

COPY pyproject.toml ./

RUN poetry export -f requirements.txt -o requirements.txt

RUN apt-get update && apt-get install cmake -y

RUN pip install -r requirements.txt

RUN apt-get clean

COPY ./app .

CMD ["python", "main.py"]