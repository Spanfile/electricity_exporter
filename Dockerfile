FROM python:latest
WORKDIR /app

COPY . .

RUN pip3 install pipenv
RUN pipenv install --system --deploy

ENV PYTHONUNBUFFERED=TRUE
ENV TZ=Europe/Helsinki

EXPOSE 8000
CMD ["python3", "-m", "gunicorn", "-b", "0.0.0.0", "electricity_exporter:app"]
