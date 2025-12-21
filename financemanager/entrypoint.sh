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
python manage.py makemigrations
python manage.py migrate --noinput

echo "Initializing database functions, views, procedures, triggers and roles..."
python << 'INIT_DB_EOF'
import os
import django
import subprocess
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'financemanager.settings')
django.setup()

from django.conf import settings

# Определяем путь к SQL файлу
# Файл должен быть в /app (в контейнере) - доступен через volume mount из financemanager/
sql_file_path = '/app/init_database_functions.sql'
if not os.path.exists(sql_file_path):
    # Альтернативный путь - относительно BASE_DIR (для локальной разработки)
    sql_file_path = os.path.join(settings.BASE_DIR, 'init_database_functions.sql')
    print(f"Trying alternative path: {sql_file_path}")

if os.path.exists(sql_file_path):
    print(f"Found SQL script at: {sql_file_path}")
    print(f"Executing SQL script: {sql_file_path}")
    
    # Получаем параметры подключения к БД из Django settings
    db_settings = settings.DATABASES['default']
    
    # Получаем параметры подключения к БД
    db_name = db_settings.get('NAME')
    db_user = db_settings.get('USER')
    db_password = db_settings.get('PASSWORD')
    db_host = db_settings.get('HOST', 'localhost')
    db_port = db_settings.get('PORT', '5432')
    
    # Пытаемся использовать psql, если доступен
    try:
        # Устанавливаем переменную окружения для пароля
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password
        
        # Выполняем SQL скрипт через psql
        result = subprocess.run(
            ['psql', '-h', db_host, '-p', str(db_port), '-U', db_user, '-d', db_name, '-f', sql_file_path],
            env=env,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Database functions, views, procedures, triggers and roles initialized successfully!")
        else:
            # Проверяем, не связана ли ошибка с уже существующими объектами
            error_output = result.stderr.lower()
            if 'already exists' in error_output or 'duplicate' in error_output:
                print("Database objects already exist. Skipping initialization.")
            else:
                print(f"Warning: Error executing SQL script:")
                print(result.stderr)
                print("Some database objects may not have been created. Continuing...")
    except FileNotFoundError:
        # Если psql не доступен, используем Python с psycopg2
        print("psql not found, using Python psycopg2...")
        try:
            from django.db import connection
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                database=db_name,
                user=db_user,
                password=db_password
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            cursor = conn.cursor()
            # Выполняем SQL команды по одной
            # Простой парсер: разбиваем по ; но учитываем строки и комментарии
            commands = []
            current_command = []
            in_string = False
            string_char = None
            in_comment = False
            
            i = 0
            while i < len(sql_content):
                char = sql_content[i]
                
                if not in_string and not in_comment:
                    if char == '-' and i + 1 < len(sql_content) and sql_content[i + 1] == '-':
                        # Начало однострочного комментария
                        in_comment = True
                        i += 2
                        continue
                    elif char == "'" or char == '"':
                        in_string = True
                        string_char = char
                        current_command.append(char)
                    elif char == ';':
                        # Конец команды
                        cmd = ''.join(current_command).strip()
                        if cmd:
                            commands.append(cmd)
                        current_command = []
                    else:
                        current_command.append(char)
                elif in_string:
                    current_command.append(char)
                    if char == string_char and (i == 0 or sql_content[i - 1] != '\\'):
                        in_string = False
                        string_char = None
                elif in_comment:
                    if char == '\n':
                        in_comment = False
                
                i += 1
            
            # Добавляем последнюю команду, если есть
            if current_command:
                cmd = ''.join(current_command).strip()
                if cmd:
                    commands.append(cmd)
            
            # Выполняем команды
            for cmd in commands:
                if cmd and not cmd.startswith('--'):
                    try:
                        cursor.execute(cmd)
                    except Exception as cmd_error:
                        error_msg = str(cmd_error).lower()
                        if 'already exists' not in error_msg and 'duplicate' not in error_msg:
                            print(f"Warning: Error in SQL command: {cmd_error}")
            
            cursor.close()
            conn.close()
            
            print("Database functions, views, procedures, triggers and roles initialized successfully!")
        except Exception as e:
            error_msg = str(e).lower()
            if 'already exists' in error_msg or 'duplicate' in error_msg:
                print("Database objects already exist. Skipping initialization.")
            else:
                print(f"Warning: Error executing SQL script: {e}")
                print("Some database objects may not have been created. Continuing...")
else:
    print(f"Warning: SQL file not found at {sql_file_path}")
    print("Skipping database functions initialization...")
INIT_DB_EOF

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

echo "Checking if default categories exist..."
python manage.py shell << EOF
from transaction.models import Category, Type

# Дефолтные категории расходов (используем ключи из SYSTEM_CATEGORY_LABELS)
expense_categories = [
    'food_dining',
    'transportation',
    'shopping',
    'bills_utilities',
    'entertainment',
    'healthcare',
    'education',
    'travel',
    'personal_care',
    'gifts_donations',
    'home_garden',
    'insurance',
    'taxes',
    'other_expenses',
]

# Дефолтные категории доходов (используем ключи из SYSTEM_CATEGORY_LABELS)
income_categories = [
    'salary',
    'freelance',
    'investment',
    'rental_income',
    'business',
    'gifts',
    'other_income',
]

# Создаем категории расходов
for category_name in expense_categories:
    # Проверяем, существует ли уже системная категория с таким именем
    if not Category.objects.filter(name=category_name, is_system=True).exists():
        Category.objects.create(
            name=category_name,
            is_system=True,
            type=Type.OUTCOME,
            user=None,
        )

# Создаем категории доходов
for category_name in income_categories:
    # Проверяем, существует ли уже системная категория с таким именем
    if not Category.objects.filter(name=category_name, is_system=True).exists():
        Category.objects.create(
            name=category_name,
            is_system=True,
            type=Type.INCOME,
            user=None,
        )

print("Default categories created successfully!")
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

