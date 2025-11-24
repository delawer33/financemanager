#!/bin/bash
set -e

echo "Waiting for database to be ready..."
python << 'WAIT_EOF'
import os
import sys
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financemanager.settings')
django.setup()

from django.db import connection
from django.db.utils import OperationalError

max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        connection.ensure_connection()
        print("Database is ready!")
        sys.exit(0)
    except OperationalError:
        attempt += 1
        if attempt < max_attempts:
            print(f"Database is unavailable - sleeping (attempt {attempt}/{max_attempts})")
            time.sleep(1)
        else:
            print("Database connection failed after maximum attempts")
            sys.exit(1)
WAIT_EOF

echo "Running migrations..."
python manage.py migrate --noinput

echo "Checking if currencies exist..."
python manage.py shell << EOF
from authapp.models import Currency
if not Currency.objects.exists():
    print("Creating initial currencies...")
    currencies = [
        {'name': 'US Dollar', 'symbol': 'USD'},
        {'name': 'Euro', 'symbol': 'EUR'},
        {'name': 'Russian Ruble', 'symbol': 'RUB'},
        {'name': 'British Pound', 'symbol': 'GBP'},
        {'name': 'Japanese Yen', 'symbol': 'JPY'},
        {'name': 'Canadian Dollar', 'symbol': 'CAD'},
        {'name': 'Australian Dollar', 'symbol': 'AUD'},
        {'name': 'Swiss Franc', 'symbol': 'CHF'},
        {'name': 'Chinese Yuan', 'symbol': 'CNY'},
        {'name': 'Indian Rupee', 'symbol': 'INR'},
        {'name': 'Brazilian Real', 'symbol': 'BRL'},
        {'name': 'South Korean Won', 'symbol': 'KRW'},
        {'name': 'Mexican Peso', 'symbol': 'MXN'},
        {'name': 'Singapore Dollar', 'symbol': 'SGD'},
        {'name': 'Hong Kong Dollar', 'symbol': 'HKD'},
        {'name': 'Norwegian Krone', 'symbol': 'NOK'},
        {'name': 'Swedish Krona', 'symbol': 'SEK'},
        {'name': 'Turkish Lira', 'symbol': 'TRY'},
        {'name': 'Polish Zloty', 'symbol': 'PLN'},
        {'name': 'Czech Koruna', 'symbol': 'CZK'},
    ]
    for currency_data in currencies:
        Currency.objects.get_or_create(
            name=currency_data['name'],
            defaults={'symbol': currency_data['symbol']}
        )
    print("Currencies created successfully!")
else:
    print("Currencies already exist.")
EOF

echo "Checking if superuser exists..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_admin=True).exists():
    import os
    from authapp.models import Currency
    
    email = os.environ.get('SUPERUSER_EMAIL', 'admin@example.com')
    password = os.environ.get('SUPERUSER_PASSWORD', 'admin123')
    firstname = os.environ.get('SUPERUSER_FIRSTNAME', 'Admin')
    lastname = os.environ.get('SUPERUSER_LASTNAME', 'User')
    currency_symbol = os.environ.get('SUPERUSER_CURRENCY', 'USD')
    
    try:
        currency = Currency.objects.get(symbol=currency_symbol)
    except Currency.DoesNotExist:
        currency = Currency.objects.first()
    
    if currency:
        user = User.objects.create_superuser(
            email=email,
            password=password,
            firstname=firstname,
            lastname=lastname,
            currency=currency
        )
        print(f"Superuser created: {email} with currency {currency.symbol}")
    else:
        print("ERROR: No currency found. Cannot create superuser.")
else:
    print("Superuser already exists.")
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec "$@"

