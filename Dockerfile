FROM python:3.7

COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt
COPY . /app
ENV UPLOAD_FOLDER /tmp

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:80", "webapp:app"]
