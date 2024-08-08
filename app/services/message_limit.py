import os
from datetime import datetime, timedelta
from fastapi import HTTPException


class MessageLimitService:
    daily_message_limit = int(os.getenv('DAILY_MESSAGE_LIMIT', 3))

    @classmethod
    def get_message_limit_text(cls, limit):
        if limit % 10 == 1 and limit % 100 != 11:
            return f"Лимит в {limit} вопрос на день."
        elif limit % 10 in [2, 3, 4] and limit % 100 not in [12, 13, 14]:
            return f"Лимит в {limit} вопроса на день."
        else:
            return f"Лимит в {limit} вопросов на день."

    @classmethod
    async def check_and_increment_question_count(cls, redis_client, user_id):
        today = datetime.now().strftime('%Y-%m-%d')
        key = f"{user_id}:{today}"

        question_count = await redis_client.get(key)
        if question_count is None:
            await redis_client.set(key, 0, ex=timedelta(days=1))
            question_count = 0
        else:
            question_count = int(question_count)

        if question_count >= cls.daily_message_limit:
            limit_message = cls.get_message_limit_text(cls.daily_message_limit)
            raise HTTPException(
                status_code=451,
                detail=f"Ошибка 451: Превышен {limit_message}."
            )

        await redis_client.incr(key)
