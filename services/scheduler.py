from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, delete
from datetime import datetime, timezone

from config.database import async_session_maker
from models.form_terms import FormTerms


scheduler = AsyncIOScheduler()


async def check_expired_forms():
    async with async_session_maker() as session:
        now = datetime.now(timezone.utc)

        result = await session.execute(
            select(FormTerms).where(FormTerms.expiry_date < now)
        )
        expired_forms = result.scalars().all()

        if expired_forms:
            print(f"Found {len(expired_forms)} expired forms")

            await session.execute(
                delete(FormTerms).where(FormTerms.expiry_date < now).execution_options(synchronize_session=False)
            )
            await session.commit()

            print("Expired forms deleted")


def start_scheduler():
    scheduler.add_job(
        check_expired_forms,
        trigger="interval",
        minutes=1,
        id="check_expired_forms",
        replace_existing=True
    )

    scheduler.start()
    print("Scheduler started")
