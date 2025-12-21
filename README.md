# Finance Manager

Django-приложение для управления личными финансами с поддержкой транзакций, категорий, счетов, бюджетов и аналитики.

## Технологии

- **Backend**: Django 5.1.6
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Processing**: Celery 5.4
- **API**: Django REST Framework
- **Containerization**: Docker & Docker Compose
- **Frontend**: HTML, CSS, JS, HTMX, ChartJS

## Требования

- Docker 20.10+
- Docker Compose 2.0+

## Быстрый старт

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий (если нужно)
git clone <repository-url>
cd financemanager

# Создайте файл .env из шаблона
cp .env-example .env
```

### 2. Настройка переменных окружения

Отредактируйте файл `.env` и укажите нужные вам параметры

### 3. Запуск приложения

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка всех сервисов
docker-compose down
```

### 4. Доступ к приложению

После успешного запуска приложение будет доступно по адресу:

- **Web**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin

**Учетные данные суперпользователя:**
- Email: значение из `SUPERUSER_EMAIL` в `.env`
- Password: значение из `SUPERUSER_PASSWORD` в `.env`

## Архитектура сервисов

Проект состоит из следующих Docker-контейнеров:

| Сервис | Описание | Порт |
|--------|----------|------|
| `web` | Django веб-приложение | 8000 |
| `db` | PostgreSQL база данных | 5432 |
| `redis` | Redis для кеша и очередей | 6379 |
| `celery` | Celery worker для фоновых задач | - |
| `celery-beat` | Celery beat для периодических задач | - |

## Полезные команды

### Управление контейнерами

```bash
# Запуск в фоновом режиме
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Просмотр статуса
docker-compose ps

# Просмотр логов конкретного сервиса
docker-compose logs -f web
docker-compose logs -f celery
```

### Работа с базой данных

```bash
# Применить миграции вручную
docker-compose exec web python manage.py migrate

# Создать суперпользователя вручную
docker-compose exec web python manage.py createsuperuser_with_currency

# Открыть Django shell
docker-compose exec web python manage.py shell

# Создать резервную копию БД
docker-compose exec db pg_dump -U postgres financemanager > backup.sql
```

### Сборка и обновление

```bash
# Пересобрать образы после изменений
docker-compose build

# Пересобрать и перезапустить
docker-compose up -d --build

# Очистить все данные
docker-compose down -v
```

## Автоматическая инициализация

При первом запуске автоматически выполняется:

1. Ожидание готовности базы данных
2. Применение миграций Django
3. Создание начальных валют (USD, EUR, RUB, GBP и др.)
4. Создание суперпользователя с указанной валютой
5. Сборка статических файлов

Полный список переменных см. в файле `.env-example`.

## Разработка

### Локальная разработка без Docker

Для разработки без Docker убедитесь, что установлены:

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env-example .env
# Отредактируйте .env

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser_with_currency

# Запуск сервера разработки
python manage.py runserver
```

## Устранение неполадок

### Проблемы с подключением к БД

```bash
# Проверка статуса БД
docker-compose exec db pg_isready -U postgres

# Просмотр логов БД
docker-compose logs db
```

### Проблемы с Redis

```bash
# Проверка Redis
docker-compose exec redis redis-cli ping

# Должен вернуть: PONG
```

### Очистка и перезапуск

```bash
# Остановить все контейнеры
docker-compose down

# Удалить все данные (осторожно!)
rm -rf var/

# Запустить заново
docker-compose up -d
```
