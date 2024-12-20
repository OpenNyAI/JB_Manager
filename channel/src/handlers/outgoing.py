import logging
import uuid
from lib.data_models import Message, Logger, ChannelLogger
from lib.channel_handler import channel_map
from ..crud import (
    get_user_by_turn_id,
    get_channel_by_turn_id,
    create_message,
)
import json
logging.basicConfig()
logger = logging.getLogger("channel")
logger.setLevel(logging.INFO)


async def send_message_to_user(turn_id: str, message: Message):
    """Send Message to user"""
    jb_user = await get_user_by_turn_id(turn_id=turn_id)
    if not jb_user:
        logger.error("User not found")
        return None
    jb_channel = await get_channel_by_turn_id(turn_id=turn_id)
    if not jb_channel:
        logger.error("Channel not found")
        return None
    channel_name: str = jb_channel.type
    channel_handler = channel_map[channel_name]
    channel_handler.send_message(channel=jb_channel, user=jb_user, message=message)
    logger.info("Message type: %s", message.message_type)
    msg_id = await create_message(
        turn_id=turn_id,
        message_type=message.message_type.value,
        is_user_sent=False,
        message=json.loads(getattr(message, message.message_type.value).model_dump_json(
            exclude_none=True
        )),
    )
    if msg_id == None:
        msg_id = str(uuid.uuid4())
        status = "No Response Created"
    else:
        status = "Success"
    channel_logger_input = Logger(
            source = "channel",
            logger_obj = ChannelLogger(
                    id = str(msg_id),
                    turn_id = turn_id,
                    channel_id = str(jb_channel.id),
                    channel_name = str(jb_channel.name),
                    msg_intent = "Outgoing",
                    msg_type = message.message_type.value,
                    sent_to_service = "Bot Output",
                    status = status
            )
    )
    logger.info("Message sent")
    return channel_logger_input
