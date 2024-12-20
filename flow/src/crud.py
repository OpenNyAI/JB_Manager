import uuid
from datetime import datetime
from typing import Dict
from sqlalchemy import join, select, update, and_
from lib.db_session_handler import DBSessionHandler
from lib.models import (
    JBFSMState,
    JBSession,
    JBWebhookReference,
    JBBot,
    JBMessage,
    JBTurn,
    JBUser,
    JBChannelLogger,
    JBApiLogger
)


async def get_state_by_session_id(session_id: str) -> JBFSMState:
    query = select(JBFSMState).where(JBFSMState.session_id == session_id)
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            state = result.scalars().first()
            return state


async def create_session(turn_id: str) -> JBSession:
    session_id = str(uuid.uuid4())
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(select(JBTurn).where(JBTurn.id == turn_id))
            jb_turn = result.scalars().first()
        async with session.begin():
            jb_session = JBSession(
                id=session_id, user_id=jb_turn.user_id, channel_id=jb_turn.channel_id
            )
            session.add(jb_session)
            await session.commit()
        async with session.begin():
            await session.execute(
                update(JBTurn).where(JBTurn.id == turn_id).values(session_id=session_id)
            )
            await session.commit()
            return jb_session


async def update_session(session_id: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            stmt = (
                update(JBSession)
                .where(JBSession.id == session_id)
                .values(updated_at=datetime.now())
            )
            await session.execute(stmt)
            await session.commit()
            return None


async def update_turn(session_id: str, turn_id: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            stmt = (
                update(JBTurn).where(JBTurn.id == turn_id).values(session_id=session_id)
            )
            await session.execute(stmt)
            await session.commit()
            return None


async def insert_state(
    session_id: str, state: str, variables: dict = dict()
) -> JBFSMState:
    state_id = str(uuid.uuid4())
    state = JBFSMState(
        id=state_id, session_id=session_id, state=state, variables=variables
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(state)
            await session.commit()
            return state
    return None


async def update_state_and_variables(
    session_id: str, state: str, variables: dict
) -> JBFSMState:
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            # await session.query(JBFSMState).filter(JBFSMState.pid == pid).update({"state": state, "variables": variables})
            stmt = (
                update(JBFSMState)
                .where(JBFSMState.session_id == session_id)
                .values(state=state, variables=variables)
            )
            await session.execute(stmt)
            await session.commit()
            return state
    return None


async def get_bot_by_session_id(session_id: str) -> JBBot | None:
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBBot)
                .select_from(
                    join(JBSession, JBTurn, JBSession.id == JBTurn.session_id).join(
                        JBBot, JBTurn.bot_id == JBBot.id
                    )
                )
                .where(JBSession.id == session_id)
            )
            s = result.scalars().first()
            return s


async def get_session_by_turn_id(turn_id: str) -> JBSession | None:
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession)
                .join(
                    JBTurn,
                    and_(
                        JBSession.user_id == JBTurn.user_id,
                        JBSession.channel_id == JBTurn.channel_id,
                    ),
                )
                .where(JBTurn.id == turn_id)
                .order_by(JBSession.updated_at.desc())
            )
            s = result.scalars().first()
            return s


async def get_all_bots():
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBBot).where(JBBot.status != "deleted")
            )
            s = result.scalars().all()
            return s


def insert_jb_webhook_reference(reference_id: str, turn_id: str):
    webhook_reference = JBWebhookReference(id=reference_id, turn_id=turn_id)

    with DBSessionHandler.get_sync_session() as session:
        with session.begin():
            session.add(webhook_reference)
            session.commit()
            return reference_id
    return False


async def create_bot(
    bot_id, name, code, requirements, index_urls, required_credentials, version
):
    bot = JBBot(
        id=bot_id,
        name=name,
        code=code,
        requirements=requirements,
        index_urls=index_urls,
        required_credentials=required_credentials,
        version=version,
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(bot)
            await session.commit()
            return bot


async def create_message(
    turn_id: str,
    message_type: str,
    message: Dict,
    is_user_sent: bool = False,
):
    message_id = str(uuid.uuid4())
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(
                JBMessage(
                    id=message_id,
                    turn_id=turn_id,
                    message_type=message_type,
                    is_user_sent=is_user_sent,
                    message=message,
                )
            )
            await session.commit()
            return message_id


async def update_user_language(turn_id: str, selected_language: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            stmt = (
                update(JBUser)
                .where(
                    JBUser.id.in_(
                        select(JBTurn.user_id)
                        .where(JBTurn.id == turn_id)
                        .scalar_subquery()
                    )
                )
                .values(language_preference=selected_language)
            )
            await session.execute(stmt)
            await session.commit()
            return None

async def get_msg_id_by_turn_id(turn_id: str, msg_intent: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBChannelLogger.id)
                .where(JBChannelLogger.turn_id == turn_id and JBChannelLogger.msg_intent == msg_intent)
            )
            msg_id = result.scalars().first()
            return msg_id

async def update_api_logger(turn_id: str,session_id: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            query = (
                update(JBApiLogger).where(JBApiLogger.turn_id == turn_id).values(session_id=session_id)
            )
            await session.execute(query)
            await session.commit()
            return None