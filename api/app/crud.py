from typing import Sequence
import logging
import uuid
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from lib.db_session_handler import DBSessionHandler
from lib.models import (
    JBWebhookReference,
    JBSession,
    JBTurn,
    JBUser,
    JBBot,
    JBChannel,
    JBApiLogger,
)

logger = logging.getLogger("jb-manager-api")

async def create_user(
    channel_id: str, phone_number: str, first_name: str, last_name: str
) -> JBUser:
    user_id = str(uuid.uuid4())
    user = JBUser(
        id=user_id,
        channel_id=channel_id,
        first_name=first_name,
        last_name=last_name,
        identifier=phone_number,
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(user)
            await session.commit()
            return user
    return None


async def get_user_by_number(number: str, channel_id: str) -> JBUser:
    query = select(JBUser).where(
        JBUser.identifier == number and JBUser.channel_id == channel_id
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            user = result.scalars().first()
            return user
    return None


async def create_turn(bot_id: str, channel_id: str, user_id: str):
    turn_id: str = str(uuid.uuid4())
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(
                JBTurn(
                    id=turn_id,
                    bot_id=bot_id,
                    channel_id=channel_id,
                    user_id=user_id,
                )
            )
            await session.commit()
            return turn_id


async def get_bot_by_id(bot_id: str):
    query = select(JBBot).options(joinedload(JBBot.channels)).where(JBBot.id == bot_id)
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            bot = result.scalars().unique().first()
            return bot


async def get_chat_history(bot_id: str, skip=0, limit=1000):
    # TODO: introduce pagination
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession, JBUser)
                .join(JBUser, JBSession.user_id == JBUser.id)
                .join(JBChannel, JBSession.channel_id == JBChannel.id)
                .where(JBChannel.bot_id == bot_id)
                .offset(skip)
                .limit(limit)
            )
            chat_history = []
            for row in result:
                chat_history.append(list(row))
            return chat_history
    return None


async def get_plugin_reference(plugin_uuid: str) -> JBWebhookReference:
    query = select(JBWebhookReference).where(JBWebhookReference.id == plugin_uuid)

    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            s = result.scalars().first()
            return s
    return None


async def get_bot_list():
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            query = (
                select(JBBot)
                .options(joinedload(JBBot.channels))
                .where(JBBot.status != "deleted")
            )
            result = await session.execute(query)
            bot_list = result.scalars().unique().all()
            return bot_list
    return None


async def get_bot_chat_sessions(bot_id: str, session_id: str):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(JBSession)
                .join(JBTurn, JBTurn.bot_id == bot_id)
                .join(JBChannel, JBSession.channel_id == JBChannel.id)
                .where(JBChannel.bot_id == bot_id)
                .options(
                    joinedload(JBSession.turns).joinedload(JBTurn.messages),
                )
                .where(JBSession.id == session_id)
            )
            chat_sessions = result.unique().scalars().all()
            return chat_sessions
    return None


async def update_bot(bot_id: str, data):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            stmt = update(JBBot).where(JBBot.id == bot_id).values(**data)
            await session.execute(stmt)
            await session.commit()
            return bot_id
    return None


async def create_bot(data):
    bot_id = str(uuid.uuid4())
    bot = JBBot(
        id=bot_id,
        name=data.get("name"),
        dsl=data.get("dsl"),
        code=data.get("code"),
        requirements=data.get("requirements"),
        index_urls=data.get("index_urls"),
        required_credentials=data.get("required_credentials"),
        version=data.get("version"),
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(bot)
            await session.commit()
            return bot


async def create_channel(bot_id, data):
    channel_id = str(uuid.uuid4())
    channel = JBChannel(
        id=channel_id,
        bot_id=bot_id,
        name=data.get("name"),
        type=data.get("type"),
        key=data.get("key"),
        app_id=data.get("app_id"),
        url=data.get("url"),
        status=data.get("status", "inactive"),
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(channel)
            await session.commit()
            return channel


async def get_channels_by_identifier(
    identifier: str, channel_type: str
) -> Sequence[JBChannel] | None:
    query = (
        select(JBChannel)
        .options(joinedload(JBChannel.bot))
        .where(
            JBChannel.app_id == identifier,
            JBChannel.type == channel_type,
            JBChannel.status != "deleted",
        )
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            channels = result.scalars().unique().all()
            return channels


async def get_active_channel_by_identifier(
    identifier: str, channel_type: str
) -> JBChannel | None:
    query = (
        select(JBChannel)
        .options(joinedload(JBChannel.bot))
        .where(
            JBChannel.app_id == identifier,
            JBChannel.type == channel_type,
            JBChannel.status == "active",
        )
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            channel = result.scalars().unique().first()
            return channel


async def get_channel_by_id(channel_id: str) -> JBChannel | None:
    query = select(JBChannel).where(JBChannel.id == channel_id)
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            result = await session.execute(query)
            channel = result.scalars().first()
            return channel


async def update_channel(channel_id: str, data):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            stmt = update(JBChannel).where(JBChannel.id == channel_id).values(**data)
            await session.execute(stmt)
            await session.commit()
            return channel_id


async def update_channel_by_bot_id(bot_id: str, data):
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            stmt = update(JBChannel).where(JBChannel.bot_id == bot_id).values(**data)
            await session.execute(stmt)
            await session.commit()
            return bot_id
