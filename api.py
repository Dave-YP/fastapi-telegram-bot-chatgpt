import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
from datetime import datetime, timedelta
from openai import AsyncOpenAI, APIError

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Установите свои ключи через переменные окружения
api_key = os.getenv('OPENAI_API_KEY')
daily_message_limit = int(os.getenv('DAILY_MESSAGE_LIMIT', 3))

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)


class Question(BaseModel):
    user_id: str
    question: str


def get_message_limit_text(limit):
    """Возвращает правильно склоненное сообщение о лимите сообщений"""
    if limit % 10 == 1 and limit % 100 != 11:
        return f"Лимит в {limit} вопрос на день."
    elif limit % 10 in [2, 3, 4] and not (limit % 100 in [12, 13, 14]):
        return f"Лимит в {limit} вопроса на день."
    else:
        return f"Лимит в {limit} вопросов на день."


@app.post("/ask")
async def ask(question: Question):
    user_id = question.user_id
    today = datetime.now().strftime('%Y-%m-%d')
    key = f"{user_id}:{today}"

    # Проверка количества вопросов, заданных пользователем
    question_count = await redis_client.get(key)
    if question_count is None:
        await redis_client.set(key, 0, ex=timedelta(days=1))
        question_count = 0
    else:
        question_count = int(question_count)

    if question_count >= daily_message_limit:
        limit_message = get_message_limit_text(daily_message_limit)
        raise HTTPException(
            status_code=451,
            detail=f"Ошибка 451: Превышен {limit_message}."
        )

    # Увеличиваем счетчик вопросов
    await redis_client.incr(key)

    try:
        # Создаем асинхронный клиент для OpenAI
        client = AsyncOpenAI(api_key=api_key)

        # Получение ответа от OpenAI
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question.question,
                }
            ],
            model="gpt-3.5-turbo",
        )

        # Получение текста ответа
        response_text = chat_completion.choices[0].message.content
        return {"response": response_text}
    except APIError as e:
        logger.error(f"Произошла ошибка при получении ответа: {str(e)}")
        if e.code == 'rate_limit_exceeded':
            raise HTTPException(
                status_code=429,
                detail="Превышен лимит запросов к API OpenAI."
            )
        elif e.code == 'unsupported_country_region_territory':
            raise HTTPException(
                status_code=403,
                detail="Ошибка 403: Ваш регион не поддерживается."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Произошла ошибка при получении ответа: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Произошла ошибка при получении ответа: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Произошла ошибка при получении ответа: {str(e)}"
        )


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
