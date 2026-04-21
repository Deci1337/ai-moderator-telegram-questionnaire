import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

DATABASE_URL = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def run_migrations():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS pride_academy"))
        await conn.run_sync(Base.metadata.create_all)

        tables_to_check = {
            "forms": [
                {"column": "user_id", "type": "BIGINT"},
                {"column": "cups", "type": "BIGINT"}
            ]
        }

        for table_name, columns in tables_to_check.items():
            for col in columns:
                try:
                    await conn.execute(text(f"""
                        ALTER TABLE pride_academy.{table_name} 
                        ALTER COLUMN {col['column']} TYPE {col['type']}
                    """))
                except Exception:
                    pass


async def init_db():
    await run_migrations()

    async with async_session_maker() as session:
        try:
            result = await session.execute(text("SELECT 1 FROM pride_academy.forms LIMIT 1"))
            result.scalar()
            print("Successfully connected to database and verified table access")
        except Exception as e:
            raise Exception(f"Database verification failed: {str(e)}")