import os
from openai import AsyncOpenAI, APIError
from fastapi import HTTPException


class OpenAIService:
    api_key = os.getenv('OPENAI_API_KEY')

    @classmethod
    async def ask_question(cls, question: str):
        try:
            client = AsyncOpenAI(api_key=cls.api_key)
            chat_completion = await client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": question,
                    }
                ],
                model="gpt-3.5-turbo",
            )
            return chat_completion.choices[0].message.content
        except APIError as e:
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
            raise HTTPException(
                status_code=500,
                detail=f"Произошла ошибка при получении ответа: {str(e)}"
            )
