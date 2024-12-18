from typing import Dict
from lib.data_models import Flow, BotConfig, FlowIntent, BotIntent, Bot
from lib.encryption_handler import EncryptionHandler
from lib.models import JBBot
from ...crud import (
    create_bot,
    get_bot_by_id,
    update_bot,
    update_channel_by_bot_id,
    get_bot_list,
    get_active_channel_by_identifier,
    create_channel,
)
from ...jb_schema import JBBotCode, JBChannelContent


async def list_bots():
    return await get_bot_list()


async def install(install_content: JBBotCode) -> Flow:
    bot_data = install_content.model_dump()
    bot = await create_bot(bot_data)
    flow_input = Flow(
        source="api",
        intent=FlowIntent.BOT,
        bot_config=BotConfig(
            bot_id=bot.id,
            intent=BotIntent.INSTALL,
            bot=Bot(
                name=install_content.name,
                fsm_code=install_content.code,
                requirements_txt=install_content.requirements,
                index_urls=install_content.index_urls,
                version = bot.version
            ),
        ),
    )
    return flow_input


async def add_credentials(bot_id: str, credentials: Dict[str, str]):
    bot = await get_bot_by_id(bot_id)
    if not bot:
        return {"status": "error", "message": "Bot not found"}
    encrypted_credentials = EncryptionHandler.encrypt_dict(credentials)
    bot_data = {"credentials": encrypted_credentials}
    await update_bot(bot_id, bot_data)
    return {"status": "success"}


async def add_channel(bot_id: str, channel_content: JBChannelContent):
    bot: JBBot = await get_bot_by_id(bot_id)
    if not bot:
        return {"status": "error", "message": "Bot not found"}
    existing_channel = await get_active_channel_by_identifier(
        identifier=channel_content.app_id, channel_type=channel_content.type
    )
    if existing_channel:
        return {
            "status": "error",
            "message": f"App ID {channel_content.app_id} already in use by bot {existing_channel.bot.name}",
        }
    channels = bot.channels
    for channel in channels:
        if (
            channel.app_id == channel_content.app_id
            and channel.type == channel_content.type
        ):
            return {
                "status": "error",
                "message": f"Bot already has an channel of type {channel_content.type} for app ID {channel_content.app_id}",
            }
    channel_content.key = EncryptionHandler.encrypt_text(channel_content.key)
    channel_data = channel_content.model_dump()
    await create_channel(bot_id, channel_data)
    return {"status": "success"}


async def delete(bot_id: str):
    bot = await get_bot_by_id(bot_id)
    if not bot:
        return {"status": "error", "message": "Bot not found"}
    bot_data = {"status": "deleted"}
    await update_bot(bot_id, bot_data)
    channel_data = {"status": "deleted"}
    await update_channel_by_bot_id(bot_id, channel_data)
    return {"status": "success"}
