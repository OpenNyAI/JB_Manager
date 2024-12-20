from sqlalchemy import select

from lib.db_session_handler import DBSessionHandler
from lib.models import JBTurn, JBUser, JBChannelLogger


async def get_user_preferred_language(turn_id: str):
    query = select(JBTurn.user_id).where(JBTurn.id == turn_id)
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            pid = result.scalars().first()
            if pid is None:
                return None
            preferred_language = await get_user_preferred_language_by_pid(pid)
            return preferred_language


async def get_user_preferred_language_by_pid(pid: str):
    query = select(JBUser.language_preference).where(JBUser.id == pid)
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            preferred_language = result.scalars().first()
            return preferred_language