import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from telegram.ext import filters, CallbackContext
import aiohttp
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен Telegram бота, URL API и лимит сообщений из переменных
telegram_token = os.getenv("TELEGRAM_TOKEN")
api_url = os.getenv("API_URL")
daily_message_limit = int(os.getenv("DAILY_MESSAGE_LIMIT", 3))

if not isinstance(api_url, str):
    raise ValueError("API_URL должна быть строкой")


def get_message_limit_text(limit):
    """Возвращает правильно склоненное сообщение о лимите сообщений"""
    if limit % 10 == 1 and limit % 100 != 11:
        return f"Ошибка 451: Превышен лимит в {limit} вопрос на день."
    elif limit % 10 in [2, 3, 4] and not (limit % 100 in [12, 13, 14]):
        return f"Ошибка 451: Превышен лимит в {limit} вопроса на день."
    else:
        return f"Ошибка 451: Превышен лимит в {limit} вопросов на день."


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        'Привет! Я бот, который обращается к Chat GPT. Задай мне вопрос.'
    )


async def handle_message(update: Update, context: CallbackContext) -> None:
    user_message = update.message.text
    logger.info(
        "Получен вопрос от пользователя %s: %s",
        update.message.chat_id,
        user_message
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                api_url,
                json={
                    "user_id": str(update.message.chat_id),
                    "question": user_message
                },
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 451:
                    error_message = get_message_limit_text(daily_message_limit)
                    await update.message.reply_text(error_message)
                elif response.status == 403:
                    await update.message.reply_text(
                        "Ошибка 403: Доступ запрещен. "
                        "Ваш регион не поддерживается."
                    )
                elif response.status == 500:
                    await update.message.reply_text(
                        "Ошибка 500: Внутренняя ошибка сервера. "
                        "Попробуйте позже."
                    )
                else:
                    response.raise_for_status()
                    data = await response.json()
                    reply_message = data.get(
                        "response",
                        "Извините, я не могу сейчас ответить на этот вопрос."
                    )
                    await update.message.reply_text(reply_message)

        except aiohttp.ClientResponseError as e:
            logger.error(f"Ошибка при запросе к API: {e.status} - {e.message}")
            if e.status == 403:
                await update.message.reply_text(
                    "Ошибка 403: Доступ запрещен. "
                    "Ваш регион не поддерживается."
                )
            else:
                await update.message.reply_text(
                    f"Ошибка при обращении к API: {e.message}"
                )

        except aiohttp.ClientConnectionError as e:
            logger.error(f"Ошибка соединения: {str(e)}")
            await update.message.reply_text(
                "Ошибка соединения с сервером. Попробуйте позже."
            )

        except aiohttp.ClientTimeout as e:
            logger.error(f"Превышено время ожидания: {str(e)}")
            await update.message.reply_text(
                "Превышено время ожидания ответа от сервера."
            )

        except Exception as e:
            logger.error(f"Произошла непредвиденная ошибка: {str(e)}")
            await update.message.reply_text(
                "Произошла непредвиденная ошибка. Попробуйте позже."
            )


def main() -> None:
    application = ApplicationBuilder().token(telegram_token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    application.run_polling()


if __name__ == "__main__":
    main()
