# ChatGPT Telegram Bot с веб-интерфейсом FastAPI

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)

## Описание

Этот проект представляет собой Telegram бота, FastAPI сервис и веб-интерфейс, которые взаимодействуют с API OpenAI для получения ответов от ChatGPT. Пользователи могут регистрироваться, входить в систему и легко переключаться между веб-интерфейсом и Telegram ботом, сохраняя свою аутентифицированную сессию. На сайте также есть возможность открыть чат с ChatGPT API.

## Ключевые особенности

- Система регистрации и аутентификации пользователей
- Веб-интерфейс для управления аккаунтом
- Плавный переход от веб-интерфейса к Telegram боту для аутентифицированных пользователей
- Интеграция с API ChatGPT от OpenAI
- Дневной лимит сообщений для пользователей
- Возможность открыть чат с GPT на сайте

## Основные компоненты

- **PostgreSQL**: Хранит данные пользователей и управляет аутентификацией.
- **Redis**: Обрабатывает кэширование и управление пользовательскими сессиями.
- **FastAPI сервис**: Обрабатывает запросы как от веб-интерфейса, так и от Telegram бота.
- **Telegram бот**: Предоставляет интерфейс чата для взаимодействия пользователей с ChatGPT.
- **Веб-интерфейс**: Позволяет пользователям регистрироваться, входить в систему и управлять своим аккаунтом.

## Требования

- Docker
- Docker Compose
- API ключ OpenAI
- Токен Telegram бота

## Установка и настройка

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/Dave-YP/fastapi-telegram-bot-chatgpt.git
   cd fastapi-telegram-bot-chatgpt
    ```

2. Настройте переменные окружения:
    Создайте файл `.env` в корне проекта и добавьте следующие переменные:

    ```env
    OPENAI_API_KEY=ваш_ключ_api_openai
    TELEGRAM_TOKEN=ваш_токен_telegram_бота
    API_URL=http://fastapi:5000
    DAILY_MESSAGE_LIMIT=3
    SECRET_KEY=ваш_секретный_ключ_для_jwt
    TELEGRAM_BOT_URL=https://t.me/your_bot_username
    ```

3. Соберите и запустите контейнеры:

    ```bash
    docker-compose up --build
    ```

## Использование

1. **Веб-интерфейс**:
    Откройте браузер и перейдите по адресу <http://localhost:5000>.
    Зарегистрируйте новый аккаунт или войдите в существующий.
    После входа вы получите ссылку на Telegram бота.

2. **Telegram бот**:
    Перейдите по предоставленной ссылке или найдите вашего бота в Telegram.
    Начните общение с ботом - вы будете автоматически аутентифицированы.

3. **Задавайте вопросы**:
    Просто отправляйте текстовые сообщения боту с вашими вопросами.
    Бот перенаправит их на FastAPI сервис, который затем запросит ответ у API OpenAI.

## Структура проекта

- **app/main.py**: Главный файл FastAPI сервиса.
- **app/api/endpoints.py**: Маршруты FastAPI сервиса, обрабатывающие запросы и взаимодействующие с API OpenAI.
- **app/bot/telegram_bot.py**: Реализация Telegram бота.
- **app/db/models.py**: Модели базы данных.
- **app/db/init_db.py**: Инициализация базы данных.
- **app/services/auth.py**: Сервисы аутентификации.
- **app/services/openai_service.py**: Сервисы для взаимодействия с OpenAI.
- **app/services/token_service.py**: Сервисы для управления токенами.
- **app/services/message_limit.py**: Сервисы для управления лимитом сообщений.
- **app/schemas/user.py**: Pydantic модели для пользователей.
- **app/schemas/token.py**: Pydantic модели для токенов.
- **app/core/config.py**: Конфигурация приложения.
- **app/core/status_codes.py**: Сообщения об ошибках и статус-коды.
- **app/templates/**: HTML шаблоны для веб-интерфейса.
    - **chat.html**: Шаблон чата.
    - **index.html**: Главная страница.
    - **login.html**: Страница входа.
    - **register.html**: Страница регистрации.
- **app/static/**: Статические файлы для веб-интерфейса.
    - **chat.js**: JavaScript файл для чата.
    - **style.css**: CSS файл для стилей.
- **Dockerfile.fastapi**: Dockerfile для FastAPI сервиса.
- **Dockerfile.bot**: Dockerfile для Telegram бота.
- **docker-compose.yml**: Конфигурация Docker Compose.

## Лицензия

Этот проект лицензирован под MIT License. Подробности смотрите в файле LICENSE.

## Конфигурация и Лимиты

- **DAILY_MESSAGE_LIMIT**: Количество вопросов, которые пользователь может задать в день. Значение по умолчанию — 3.
- **SECRET_KEY**: Используется для шифрования JWT токена (убедитесь, что он безопасен и уникален).

## Контакты

Если у вас возникли проблемы или есть вопросы, пожалуйста, создайте issue в GitHub репозитории или свяжитесь с автором проекта.
