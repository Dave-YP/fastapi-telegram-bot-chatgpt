import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from openai import AsyncOpenAI, APIError

from db import User, get_db


class AuthService:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 120

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    @classmethod
    def create_access_token(
        cls, data: dict,
        expires_delta: Optional[timedelta] = None
    ):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            cls.SECRET_KEY,
            algorithm=cls.ALGORITHM
        )
        return encoded_jwt

    @classmethod
    async def authenticate_user(
        cls,
        db: AsyncSession,
        email: str,
        password: str
    ):
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not cls.pwd_context.verify(
            password,
            user.hashed_password
        ):
            return False
        return user

    @classmethod
    async def get_current_user(cls, request: Request, db: AsyncSession):
        credentials_exception = HTTPException(
            status_code=401,
            detail="Не удалось подтвердить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )

        token = (
            request.cookies.get("access_token") or
            request.headers.get("Authorization")
        )
        if not token:
            raise credentials_exception

        try:
            token = (
                token.split()[1]
                if token.lower().startswith("bearer ")
                else token
            )
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user

    @classmethod
    async def get_current_user_for_chat(
        cls, token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ):
        credentials_exception = HTTPException(
            status_code=401,
            detail="Не удалось подтвердить учетные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM]
            )
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        return user


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
