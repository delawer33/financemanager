### Финансовый менеджер (в разработке)

Для того, чтобы запустить приложение, нужно:
- установить зависимости из requirements.txt
- создать файл .env в корневой папке проекта (где лежит manage.py) по шаблону `.env.example`, который лежит в той же папке
- запустить сервер (python3 manage.py runserver)
- если нужно, чтобы работали регулярные транзакции, тогда параллельно запустить celery `celery -A financemanager worker --loglevel=info | celery -A financemanager beat --loglevel=info` (для linux) (также должен быть установлен `redis`)

