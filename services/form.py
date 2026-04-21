from datetime import datetime

from models import Form, FormTerms
from sqlalchemy import select, and_, exists, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
from config.database import async_session_maker
from models.form_likes import FormLikes

from .telegram import send_message


async def get_form(
        user_id: int
) -> Form:
    async with async_session_maker() as session:
        stmt = select(Form).where(Form.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one()


async def create_form(
        user_id: int,
        cups: int = None,
        photo_id: str = None,
        description: str = None,
        searchs: str = None,
        tier: str = None,
        rank: str = None,
        league_rank: int = None
) -> Form:
    async with async_session_maker() as session:
        try:
            result = await session.execute(
                select(Form).where(Form.user_id == user_id)
            )
            form = result.scalar_one_or_none()

            if form:
                if cups is not None:
                    form.cups = cups
                if photo_id is not None:
                    form.photo_id = photo_id
                if description is not None:
                    form.description = description
                if searchs is not None:
                    form.searchs = searchs
                if tier is not None:
                    form.tier = tier
                if rank is not None:
                    form.rank = rank
                if league_rank is not None:
                    form.league_rank = league_rank

            else:
                form = Form(
                    user_id=user_id,
                    cups=cups,
                    photo_id=photo_id,
                    description=description,
                    searchs=searchs,
                    tier=tier,
                    rank=rank,
                    league_rank=league_rank
                )
                session.add(form)

            await session.commit()
            await session.refresh(form)

            return form

        except Exception as e:
            await session.rollback()
            raise e


async def update_form(
        form_id: int,
        **kwargs
) -> Form:
    async with async_session_maker() as session:
        try:
            query = select(Form).where(Form.id == form_id)
            result = await session.execute(query)
            form = result.scalar_one_or_none()

            if not form:
                return None

            for key, value in kwargs.items():
                if hasattr(form, key) and value is not None:
                    setattr(form, key, value)

            await session.commit()
            await session.refresh(form)

            return form

        except Exception as e:
            await session.rollback()
            raise e


async def delete_form(
        form_id: int
) -> bool:
    async with async_session_maker() as session:
        try:
            query = select(Form).where(Form.id == form_id)
            result = await session.execute(query)
            form = result.scalar_one_or_none()

            if not form:
                return False

            await session.delete(form)
            await session.commit()

            return True

        except Exception as e:
            await session.rollback()
            raise e


async def check_form_exists(user_id: int) -> bool:
    async with async_session_maker() as session:
        stmt = select(
            exists().where(Form.user_id == user_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()


async def get_random_form_excluding_terms(user_id: int):
    async with async_session_maker() as session:
        stmt = (
            select(Form)
            .where(
                Form.user_id != user_id,
                ~exists().where(
                    and_(
                        FormTerms.form_id == Form.id,
                        FormTerms.user_id == user_id,
                        FormTerms.expiry_date > func.now()
                    )
                )
            )
            .order_by(func.random())
            .limit(1)
        )

        result = await session.execute(stmt)
        return result.scalars().first()


async def create_form_term(
        user_id: int,
        form_id: int,
        expiry_date: datetime,
) -> Form:
    async with async_session_maker() as session:
        try:
            new_form = FormTerms(
                user_id=user_id,
                form_id=form_id,
                expiry_date=expiry_date,
            )

            session.add(new_form)
            await session.commit()
            await session.refresh(new_form)

            return new_form

        except Exception as e:
            await session.rollback()
            raise e


async def create_form_like(user_id, form_id, liked_user_id) -> bool:
    async with async_session_maker() as session:
        stmt = insert(FormLikes).values(
            user_id=user_id,
            form_id=form_id,
            liked_user_id=liked_user_id
        ).on_conflict_do_nothing(constraint='uq_user_form_like')
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0


async def get_random_form_and_like_by_user_id(user_id: int):
    async with async_session_maker() as session:
        stmt = (
            select(Form, FormLikes)
            .join(FormLikes, Form.user_id == FormLikes.liked_user_id)
            .where(FormLikes.user_id == user_id)
            .order_by(func.random())
            .limit(1)
        )

        result = await session.execute(stmt)
        row = result.first()

        if row:
            return row.Form, row.FormLikes
        return None, None


async def delete_likes_by_liked_user_id(liked_user_id: int):
    async with async_session_maker() as session:
        stmt = (
            delete(FormLikes)
            .where(FormLikes.liked_user_id == liked_user_id)
        )

        await session.execute(stmt)
        await session.commit()
