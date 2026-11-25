FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git libimage-exiftool-perl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir celery redis sqlalchemy sherlock-project maigret
COPY app ./app
CMD ["celery","-A","app.worker.celery_app","worker","--loglevel=INFO","--concurrency=2"]
