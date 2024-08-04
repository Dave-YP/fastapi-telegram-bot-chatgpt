import os
import logging

import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from telegram.ext import ConversationHandler, CallbackContext, filters

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelень)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
telegram_token = os.getenv("TELEGRAM_TOKEN")
api_url = os.getenv("API_URL")
daily_message_limit = int(os.getenv("DAILY_MESSAGE_LIMIT", 3))

if not telegram_token:
    raise ValueError("TELEGRAM_TOKEN должен быть предоставлен")
if not api_url:
    raise ValueError("API_URL должен быть предоставлен")

REGISTER_EMAIL, REGISTER_PASSWORD, LOGIN_EMAIL, LOGIN_PASSWORD = range(4)
user_sessions = {}


def get_message_limit_text(limit):
    if limit % 10 == 1 and limit % 100 != 11:
        return f"Ошибка 451: Достигнут дневной лимит в {limit} вопрос."
    elif limit % 10 in [2, 3, 4] and not (limit % 100 in [12, 13, 14]):
        return f"Ошибка 451: Достигнут дневной лимит в {limit} вопроса."
    else:
        return f"Ошибка 451: Достигнут дневной лимит в {limit} вопросов."


async def handle_auth_token(update: Update, context: CallbackContext) -> None:
    auth_token = context.args[0] if context.args else None
    if not auth_token:
        await update.message.reply_text(
            "Пожалуйста, используйте ссылку "
            "с сайта для автоматической авторизации."
        )
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{api_url}/verify_token",
                json={"token": auth_token}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    user_sessions[update.message.chat_id] = {
                        "token": data["access_token"],
                        "email": data["email"],
                        "message_count": 0
                    }
                    await update.message.reply_text(
                        "Вы успешно авторизованы. "
                        "Теперь вы можете задавать вопросы."
                    )
                else:
                    await update.message.reply_text(
                        "Неверный или устаревший токен. "
                        "Пожалуйста, войдите через сайт."
                    )
        except Exception as e:
            await handle_api_error(update, str(e))


async def start(update: Update, context: CallbackContext) -> None:
    if context.args:
        await handle_auth_token(update, context)
    else:
        await update.message.reply_text(
            "Привет! Я бот для ответов на ваши вопросы. "
            "Используйте команду /register для регистрации, "
            "/login для входа и /logout для выхода из системы."
        )


async def register(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Пожалуйста, введите вашу электронную почту для регистрации:"
    )
    return REGISTER_EMAIL


async def get_register_email(update: Update, context: CallbackContext) -> int:
    user_sessions[update.message.chat_id] = {"email": update.message.text}
    await update.message.reply_text("Теперь введите ваш пароль:")
    return REGISTER_PASSWORD


async def handle_api_error(update: Update, error_message: str):
    logger.error(f"Ошибка API: {error_message}")
    await update.message.reply_text(f"Произошла ошибка: {error_message}")


async def get_register_password(
    update: Update,
    context: CallbackContext
) -> int:
    user_data = user_sessions[update.message.chat_id]
    password = update.message.text

    if len(password) < 6:
        await update.message.reply_text(
            "Пароль должен содержать минимум 6 символов."
        )
        return REGISTER_PASSWORD

    user_data["password"] = password
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{api_url}/register",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "message": ""
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    await update.message.reply_text(data["message"])
                elif response.status == 400:
                    await update.message.reply_text(
                        "Электронная почта уже зарегистрирована."
                    )
                else:
                    error_data = await response.json()
                    await handle_api_error(
                        update, error_data.get("detail", "Неизвестная ошибка")
                    )
        except Exception as e:
            await handle_api_error(update, str(e))
    user_sessions.pop(update.message.chat_id, None)
    return ConversationHandler.END


async def login(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Пожалуйста, введите вашу "
        "электронную почту для входа:")
    return LOGIN_EMAIL


async def logout(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id in user_sessions:
        user_sessions.pop(chat_id, None)
        await update.message.reply_text("Вы успешно вышли из системы.")
    else:
        await update.message.reply_text("Вы не были авторизованы.")


async def get_login_email(update: Update, context: CallbackContext) -> int:
    user_sessions[update.message.chat_id] = {"email": update.message.text}
    await update.message.reply_text("Теперь введите ваш пароль:")
    return LOGIN_PASSWORD


async def get_login_password(update: Update, context: CallbackContext) -> int:
    user_data = user_sessions[update.message.chat_id]
    password = update.message.text

    if len(password) < 6:
        await update.message.reply_text(
            "Пароль должен содержать "
            "минимум 6 символов."
        )
        return LOGIN_PASSWORD

    user_data["password"] = password
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{api_url}/token",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    user_sessions[update.message.chat_id]["token"] = (
                        data["access_token"]
                    )
                    user_sessions[update.message.chat_id]["message_count"] = 0
                    await update.message.reply_text(
                        "Успешный вход. Теперь вы можете задавать вопросы."
                    )
                else:
                    error_data = await response.json()
                    await handle_api_error(
                        update, error_data.get("detail", "Неизвестная ошибка")
                    )
        except Exception as e:
            await handle_api_error(update, str(e))
    return ConversationHandler.END


async def answer_question(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    if chat_id not in user_sessions or "token" not in user_sessions[chat_id]:
        await update.message.reply_text(
            "Пожалуйста, войдите с помощью команды /login."
        )
        return

    question_text = update.message.text
    logger.info(f"Получен вопрос от chat_id {chat_id}: {question_text}")

    async with aiohttp.ClientSession() as session:
        try:
            headers = {
                "Authorization": f"Bearer {user_sessions[chat_id]['token']}"
            }
            logger.info(
                "Отправка запроса на /ask с данными: "
                "{'user_id': str(chat_id), 'question': question_text}"
            )
            async with session.post(
                f"{api_url}/ask",
                headers=headers,
                json={"user_id": str(chat_id), "question": question_text},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    reply_message = data.get(
                        "response",
                        "Извините, я не могу ответить "
                        "на этот вопрос прямо сейчас."
                    )
                    await update.message.reply_text(reply_message)
                elif response.status == 401:
                    await update.message.reply_text(
                        "Ваша сессия истекла. Пожалуйста, "
                        "войдите снова с помощью команды /login."
                    )
                    user_sessions.pop(chat_id, None)
                elif response.status == 422:
                    error_data = await response.json()
                    logger.error(f"Ошибка валидации: {error_data}")
                    await update.message.reply_text(
                        "Ошибка 422: Неверный запрос. Пожалуйста, "
                        "попробуйте снова или обратитесь в поддержку."
                    )
                elif response.status == 451:
                    error_message = get_message_limit_text(daily_message_limit)
                    await update.message.reply_text(error_message)
                elif response.status == 403:
                    await update.message.reply_text(
                        "Ошибка 403: Запрещено. Ваш регион не поддерживается."
                    )
                elif response.status == 500:
                    await update.message.reply_text(
                        "Ошибка 500: Внутренняя ошибка сервера. "
                        "Пожалуйста, попробуйте позже."
                    )
                else:
                    await update.message.reply_text(
                        f"Неожиданная ошибка: HTTP {response.status}"
                    )

        except aiohttp.ClientResponseError as e:
            logger.error(f"Ошибка запроса API: {e.status} - {e.message}")
            await update.message.reply_text(f"Ошибка запроса API: {e.message}")

        except aiohttp.ClientConnectionError as e:
            logger.error(f"Ошибка соединения: {str(e)}")
            await update.message.reply_text(
                "Ошибка соединения с сервером. Пожалуйста, попробуйте позже."
            )

        except aiohttp.ClientTimeout as e:
            logger.error(f"Ошибка таймаута: {str(e)}")
            await update.message.reply_text("Таймаут ответа сервера.")

        except Exception as e:
            logger.error(f"Неожиданная ошибка: {str(e)}")
            await update.message.reply_text(
                "Произошла неожиданная ошибка. Пожалуйста, попробуйте позже."
            )


def main() -> None:
    application = ApplicationBuilder().token(telegram_token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("register", register),
            CommandHandler("login", login)
        ],
        states={
            REGISTER_EMAIL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_register_email
                )
            ],
            REGISTER_PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_register_password
                )
            ],
            LOGIN_EMAIL: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_login_email
                )
            ],
            LOGIN_PASSWORD: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_login_password
                )
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, answer_question)
    )

    application.run_polling()


if __name__ == '__main__':
    main()
