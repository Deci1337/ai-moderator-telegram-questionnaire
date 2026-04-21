import asyncio
import os
import sys
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from config.database import init_db
from config.bot import bot, dp
from routes.routes import setup_routes

from handlers import register_handlers

from services.scheduler import start_scheduler, scheduler
from migrations import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting bot service...")

    run_migrations()

    await init_db()

    dp.include_router(register_handlers())

    start_scheduler()

    asyncio.create_task(dp.start_polling(bot))
    print("Bot polling started")

    yield

    print("Shutting down bot service...")
    scheduler.shutdown()
    await bot.session.close()


def create_app() -> FastAPI:
    load_dotenv()

    required_env_vars = ["DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT", "BOT_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    """
    Create and configure FastAPI application
    """
    app = FastAPI(
        title="Telegram Bot Service",
        description="Microservice for Telegram bot with FastAPI and aiogram3",
        version="1.0.0",
        lifespan=lifespan
    )

    setup_routes(app)

    return app


if __name__ == "__main__":
    app = create_app()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info"
    )
