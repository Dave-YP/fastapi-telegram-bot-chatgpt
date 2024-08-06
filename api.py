import os
import logging
from datetime import timedelta

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from dotenv import load_dotenv
import aioredis
import secrets

from db import get_db, User, init_db
from services import AuthService, OpenAIService, MessageLimitService
from schemas import Token, RegisterUser, Question
from status_codes import StatusMessages

load_dotenv()

TELEGRAM_BOT_URL = os.getenv("TELEGRAM_BOT_URL")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
daily_message_limit = int(os.getenv("DAILY_MESSAGE_LIMIT", 3))
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Замените на конкретные домены в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Инициализация Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)


@app.on_event("startup")
async def startup_event():
    await init_db()


def generate_bot_token(user_id: int) -> str:
    return secrets.token_urlsafe(32)


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        current_user = await AuthService.get_current_user(request, db)
        return templates.TemplateResponse(
            "chat.html",
            {"request": request,
             "current_user": current_user}
        )
    except HTTPException:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/chat")
async def chat(
    message: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        current_user = await AuthService.get_current_user(request, db)
    except HTTPException:
        raise HTTPException(status_code=401, detail=StatusMessages.UNAUTHORIZED)

    user_id = current_user.id

    if len(message['message']) > 1000:
        return {"response": "Максимальная длина сообщения - 1000 символов.", "error": True}

    try:
        await MessageLimitService.check_and_increment_question_count(
            redis_client,
            user_id
        )
    except HTTPException:
        limit_message = StatusMessages.get_message_limit_text(daily_message_limit)
        return {"response": limit_message, "error": True}

    try:
        response_text = await OpenAIService.ask_question(message['message'])
        return {"response": response_text}
    except HTTPException as e:
        if e.status_code == 401:
            return {"response": StatusMessages.SESSION_EXPIRED, "error": True}
        elif e.status_code == 422:
            return {"response": StatusMessages.VALIDATION_ERROR, "error": True}
        elif e.status_code == 451:
            return {"response": StatusMessages.get_message_limit_text(daily_message_limit), "error": True}
        elif e.status_code == 403:
            return {"response": StatusMessages.FORBIDDEN, "error": True}
        elif e.status_code == 500:
            return {"response": StatusMessages.SERVER_ERROR, "error": True}
        else:
            return {"response": StatusMessages.UNEXPECTED_ERROR.format(status=e.status_code), "error": True}

    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=StatusMessages.SERVER_ERROR)


def get_message_limit_text(limit):
    if limit % 10 == 1 and limit % 100 != 11:
        return f"Ошибка 451: Достигнут дневной лимит в {limit} вопрос."
    elif limit % 10 in [2, 3, 4] and not (limit % 100 in [12, 13, 14]):
        return f"Ошибка 451: Достигнут дневной лимит в {limit} вопроса."
    else:
        return f"Ошибка 451: Достигнут дневной лимит в {limit} вопросов."


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        current_user = await AuthService.get_current_user(request, db)
        context = {
            "request": request,
            "current_user": current_user,
            "telegram_bot_url": TELEGRAM_BOT_URL
        }

        if current_user:
            bot_token = generate_bot_token(current_user.id)
            await redis_client.setex(
                f"bot_token:{bot_token}", 3600, str(current_user.id)
            )
            context["bot_token"] = bot_token

        return templates.TemplateResponse("index.html", context)
    except HTTPException:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "current_user": None,
                "telegram_bot_url": TELEGRAM_BOT_URL
            }
        )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    registered = request.query_params.get("registered", "false") == "true"
    return templates.TemplateResponse(
        "login.html", {"request": request, "registered": registered}
    )


@app.post("/login")
async def login(
    request: Request, email: str = Form(...), password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.authenticate_user(db, email, password)
    if not user:
        return JSONResponse(
            content={"error": "Неверный email или пароль"}, status_code=400
        )

    access_token_expires = timedelta(
        minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response = JSONResponse(content={"success": True, "redirect": "/"})
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register/form")
async def register_user_form(
    request: Request, email: str = Form(...), password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).filter(User.email == email))
    db_user = result.scalar_one_or_none()
    if db_user:
        return JSONResponse(
            content={"error": "Email уже зарегистрирован"}, status_code=400
        )

    hashed_password = AuthService.pwd_context.hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        return JSONResponse(
            content={"success": True, "redirect": "/login?registered=true"}
        )
    except IntegrityError:
        await db.rollback()
        return JSONResponse(
            content={"error": "Произошла ошибка при регистрации. "
                              "Пожалуйста, попробуйте еще раз."},
            status_code=400
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при регистрации пользователя: {str(e)}")
        return JSONResponse(
            content={"error": "Произошла внутренняя ошибка сервера. "
                              "Пожалуйста, попробуйте позже."},
            status_code=500
        )


@app.post("/register", response_model=RegisterUser)
async def register_user(
    register_user: RegisterUser, db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(User).filter(User.email == register_user.email)
        )
        db_user = result.scalar_one_or_none()
        if db_user:
            raise HTTPException(
                status_code=400,
                detail="Email уже зарегистрирован"
            )

        hashed_password = AuthService.pwd_context.hash(register_user.password)
        new_user = User(
            email=register_user.email,
            hashed_password=hashed_password
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return {
            "email": register_user.email,
            "password": "********",
            "message": "Пользователь успешно зарегистрирован"
        }
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email уже существует"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при регистрации: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Внутренняя ошибка сервера"
        )


@app.post("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Проверка состояния не удалась: {str(e)}")
        return {
            "status": "unhealthy", "database": "disconnected", "error": str(e)
        }


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await AuthService.authenticate_user(
        db, form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/refresh_token", response_model=Token)
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        current_user = await AuthService.get_current_user(request, db)
    except HTTPException:
        raise HTTPException(
            status_code=401,
            detail="Недействительный токен для обновления",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(
        minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = AuthService.create_access_token(
        data={"sub": current_user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/verify_token")
async def verify_token(token_data: dict, db: AsyncSession = Depends(get_db)):
    token = token_data.get("token")
    if not token:
        raise HTTPException(
            status_code=400,
            detail="Токен не предоставлен"
        )

    user_id = await redis_client.get(f"bot_token:{token}")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Неверный или устаревший токен"
        )

    user = await db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    access_token_expires = timedelta(
        minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "email": user.email}


@app.post("/ask")
async def ask(
    question: Question,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Получен запрос на /ask: {question.question}")
    try:
        current_user = await AuthService.get_current_user(request, db)
        logger.info(f"Пользователь аутентифицирован: {current_user.email}")
    except HTTPException as e:
        logger.error(f"Ошибка аутентификации: {str(e)}")
        raise e
    user_id = current_user.id

    if len(question.question) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Максимальная длина вопроса - 1000 символов."
        )

    try:
        await MessageLimitService.check_and_increment_question_count(
            redis_client, user_id
        )
    except HTTPException as e:
        raise e

    try:
        response_text = await OpenAIService.ask_question(question.question)
        return {"response": response_text}
    except HTTPException as e:
        raise e


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
