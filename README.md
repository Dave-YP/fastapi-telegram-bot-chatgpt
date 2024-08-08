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
- Веб-интерфейс для управления аккаунтом.
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

- **api.py**: FastAPI сервис, обрабатывающий запросы и взаимодействующий с API OpenAI. Поддерживает лимит на количество вопросов в день, и токены на сообщения, обрабатывающий запросы веб-интерфейса и бота.
- **bot.py**: Реализация Telegram бота.
- **db.py**: Модели базы данных и инициализация.
- **services.py**: Сервисы аутентификации, OpenAI и лимита сообщений.
- **schemas.py**: Pydantic модели для валидации запросов/ответов.
- **templates/**: HTML шаблоны для веб-интерфейса.
- **static/**: Статические файлы для веб-интерфейса.
- **Dockerfile.fastapi**: Dockerfile для FastAPI сервиса и Telegram бота.
- **docker-compose.yml**: Конфигурация Docker Compose.

## Лицензия

Этот проект лицензирован под MIT License. Подробности смотрите в файле LICENSE.

## Конфигурация и Лимиты

- **DAILY_MESSAGE_LIMIT**: Количество вопросов, которые пользователь может задать в день. Значение по умолчанию — 3.
- **SECRET_KEY**: Используется для шифрования JWT токена (убедитесь, что он безопасен и уникален).

## Контакты

Если у вас возникли проблемы или есть вопросы, пожалуйста, создайте issue в GitHub репозитории или свяжитесь с автором проекта.
