import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import aioredis
import secrets

from app.db.init_db import init_db
from app.core.config import settings
from app.api.endpoints import router

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
daily_message_limit = settings.DAILY_MESSAGE_LIMIT
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Инициализация Redis
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)


@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("Application startup complete.")


def generate_bot_token(user_id: int) -> str:
    return secrets.token_urlsafe(32)


app.include_router(router)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
