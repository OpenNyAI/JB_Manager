from sqlalchemy import select
from lib.db_session_handler import DBSessionHandler
from lib.models import (
    JBFlowLogger
)

async def get_msg_id_by_turn_id(turn_id: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBFlowLogger.msg_id)
                .where(JBFlowLogger.turn_id == turn_id and JBFlowLogger.sent_to_service == "Retriever")
            )
            msg_id = result.scalars().first()
            return msg_id