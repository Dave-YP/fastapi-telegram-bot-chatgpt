import os

import logging
import requests

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from telegram.ext import ContextTypes, filters

# Вставьте ваш токен, выданный @BotFather
TOKEN = os.getenv('TELEGRAM_TOKEN')
# URL вашего FastAPI сервиса в Docker сети
API_URL = os.getenv('API_URL', 'http://fastapi:5000/ask')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /start.

    :param update: Объект Update.
    :param context: Объект ContextTypes.DEFAULT_TYPE.
    """
    logger.info('Команда /start получена')
    await update.message.reply_text(
        'Привет! Я бот, который обращается к Chat GPT. Задай мне вопрос.'
    )


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Обрабатывает текстовые сообщения от пользователей.

    :param update: Объект Update.
    :param context: Объект ContextTypes.DEFAULT_TYPE.
    """
    question = update.message.text
    user_id = update.message.from_user.id
    logger.info(f'Получен вопрос от пользователя {user_id}: {question}')
    try:
        # Добавление таймаута для запроса
        response = requests.post(
            API_URL, json={'user_id': str(user_id), 'question': question},
            timeout=10
        )
        response.raise_for_status()  # Проверка успешного выполнения запроса
        answer = response.json().get(
            'response',
            'Извини, я не смог получить ответ.'
        )
        logger.info(f'Ответ: {answer}')
    except requests.Timeout as e:
        logger.error(f'Таймаут при запросе к API: {e}')
        answer = 'Произошла ошибка таймаута при попытке связаться с сервером.'
    except requests.RequestException as e:
        logger.error(f'Ошибка при запросе к API: {e}')
        answer = 'Произошла ошибка при попытке связаться с сервером.'
    except ValueError as e:
        logger.error(f'Ошибка при декодировании JSON: {e}')
        answer = 'Произошла ошибка при обработке ответа от сервера.'
    await update.message.reply_text(answer)


def main():
    logger.info('Запуск бота')
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND,
                       handle_message)
    )

    application.run_polling()


if __name__ == '__main__':
    main()
