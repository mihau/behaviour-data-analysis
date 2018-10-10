FROM python:3.7-alpine

COPY requirements.txt /app
WORKDIR /app

RUN pip install -r requirements.txt
COPY . /app

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:80", "webapp:app"]
