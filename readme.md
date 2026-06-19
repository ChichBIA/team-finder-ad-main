**TeamFinder**


# Технологии
Python 3.12+
Django 5.2
PostgreSQL
Pillow (генерация аватаров)
python-decouple (настройки через .env)
Локальный запуск

## 1. Виртуальное окружение
`python -m venv venv`

## Активация:

# Windows (PowerShell): 
`venv\Scripts\Activate.ps1`
# Windows (cmd):
 `venv\Scripts\activate`
# Linux/Mac:
 `source venv/bin/activate`


## Установка зависимостей:
 `pip install -r requirements.txt`


## 2. Файл .env

# Скопируйте пример и укажите параметры окружения:
 `cp .env_example .env`

# Пример заполнения .env:
DJANGO_SECRET_KEY=change_me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=team_finder
POSTGRES_USER=team_finder
POSTGRES_PASSWORD=team_finder
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

TASK_VERSION=1`

## 3. PostgreSQL через Docker

# Запуск: 
`docker compose up -d`

# Остановить контейнеры:
 `docker compose down`

## 4. Миграции
`python manage.py migrate`

5. ## Тестовые данные (опционально)

# Команда создаёт нескольких пользователей и проекты:
 `python manage.py seed_demo`

# Данные для входа (пароль одинаковый):
anton@example.com / demo12345
dmitriy@example.com / demo12345
lector@example.com / demo12345

# Создание пользователя с доступом в Админ-панель:
 `python manage.py createsuperuser`

## 6. Запуск сервера
`python manage.py runserver`

# Проект доступен по адресу: *http://localhost:8000*

# Запуск тестов
`python manage.py test`
