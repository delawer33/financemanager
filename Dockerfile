FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY financemanager/ .

COPY financemanager/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY financemanager/init_database_functions.sql /app/init_database_functions.sql

RUN mkdir -p /app/staticfiles

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=financemanager.settings

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

