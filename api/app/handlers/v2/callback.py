import logging
from typing import Dict, AsyncGenerator, Optional, Tuple
from lib.channel_handler import ChannelHandler
from lib.data_models import Channel, ChannelIntent, RestBotInput, Logger, APILogger
from ...crud import (
    get_active_channel_by_identifier,
    get_user_by_number,
    create_user,
    create_turn,
)

logger = logging.getLogger("jb-manager-api")
logger.setLevel(logging.DEBUG)


async def handle_callback(
    bot_identifier: str,
    callback_data: Dict,
    headers: Dict,
    query_params: Dict,
    chosen_channel: type[ChannelHandler],
)-> AsyncGenerator[Tuple[Optional[ValueError], Optional[Channel]], None]:
    for channel_data in chosen_channel.process_message(callback_data):
        user = channel_data.user
        message_data = channel_data.message_data

        jb_channel = await get_active_channel_by_identifier(
            bot_identifier, chosen_channel.get_channel_name()
        )
        if jb_channel is None:
            logger.error("Active channel not found for identifier %s", bot_identifier)
            api_logger_input = Logger(
                source = "api",
                logger_obj = APILogger(
                    user_id = "User identifier:" + user.user_identifier,
                    turn_id = " ",
                    session_id = " ",
                    status = "Active channel not found for given bot identifier",
                )
            ) 
            yield ValueError("Active channel not found"), None, api_logger_input

        bot_id: str = jb_channel.bot_id
        channel_id: str = jb_channel.id

        jb_user = await get_user_by_number(user.user_identifier, channel_id=channel_id)
        if jb_user is None:
            # register user
            logger.info("Registering user")
            jb_user = await create_user(
                channel_id, user.user_identifier, user.user_name, user.user_name
            )

        user_id: str = jb_user.id
        turn_id = await create_turn(
            bot_id=bot_id, channel_id=channel_id, user_id=user_id
        )
        channel_input = Channel(
            source="api",
            turn_id=turn_id,
            intent=ChannelIntent.CHANNEL_IN,
            bot_input=RestBotInput(
                channel_name=chosen_channel.get_channel_name(),
                headers=headers,
                data=message_data,
                query_params=query_params,
            ),
        )

        if channel_input:
            status = "Success"
        else:
            status = "Channel input object not created"
        api_logger_input = Logger(
            source = "api",
            logger_obj = APILogger(
                    user_id = user_id,
                    turn_id = turn_id,
                    session_id = " ",
                    status = status,
            )
        ) 
        yield None, channel_input , api_logger_input
