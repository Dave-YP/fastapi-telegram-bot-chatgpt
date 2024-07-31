from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
from datetime import datetime, timedelta
import os
from openai import AsyncOpenAI
import logging

app = FastAPI()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Установите свой ключ OpenAI API через переменную окружения
api_key = os.getenv('OPENAI_API_KEY')

# Подключение к Redis
redis_client = redis.Redis(host='redis', port=6379, db=0)


class Question(BaseModel):
    user_id: str
    question: str


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

    if question_count >= 3:
        raise HTTPException(
            status_code=429,
            detail="Лимит в 3 вопроса на день."
        )

    # Увеличиваем счетчик вопросов
    await redis_client.incr(key)

    try:
        # Создаем асинхронный клиент для OpenAI с таймаутом
        client = AsyncOpenAI(api_key=api_key, timeout=10.0)

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
        response_text = chat_completion['choices'][0]['message']['content']
        return {"response": response_text}
    except Exception as e:
        logger.error(f"Произошла ошибка при получении ответа: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Произошла ошибка при получении ответа: {str(e)}"
        )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
