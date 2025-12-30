FROM python:3.13.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["flask", "--app", "app.app", "run", "--host=0.0.0.0"]

LABEL org.opencontainers.image.title="Docker Weather Dashboard" \
      org.opencontainers.image.version="2.1.2" \
      org.opencontainers.image.source="https://github.com/fish906/weather-dashboard"
