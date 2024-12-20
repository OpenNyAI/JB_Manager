import base64
import uuid
import logging
from lib.data_models import (
    RestBotInput,
    Flow,
    FlowIntent,
    UserInput,
    Dialog,
    Message,
    MessageType,
    Language,
    LanguageIntent,
    AudioMessage,
    Logger,
    ChannelLogger,
)
from lib.channel_handler import channel_map, ChannelHandler
from lib.file_storage import StorageHandler
from ..crud import get_channel_by_turn_id

logging.basicConfig()
logger = logging.getLogger("channel")
logger.setLevel(logging.INFO)

async def create_channel_logger_input(turn_id: str, 
                                      channel_id: str, 
                                      channel_name: str,
                                      message_type: str, 
                                      sent_to_service: str):
    if message_type == "Not Implemented":
        status = "Message object not created"
    else:
        status = "Success"
    id = str(uuid.uuid4())
    channel_logger_input = Logger(
            source = "channel",
            logger_obj = ChannelLogger(
                    id = id,
                    turn_id = turn_id,
                    channel_id = channel_id,
                    channel_name = channel_name,
                    msg_intent = "Incoming",
                    msg_type = message_type,
                    sent_to_service = sent_to_service,
                    status = status
            )
    )
    return channel_logger_input

async def process_incoming_messages(turn_id: str, bot_input: RestBotInput):
    """Process incoming messages"""
    channel = channel_map[bot_input.channel_name]
    jb_channel = await get_channel_by_turn_id(turn_id)

    message_type = channel.get_message_type(bot_input)
    logger.info("Message type: %s", message_type)

    if message_type == MessageType.TEXT:
        text_message = channel.to_text_message(bot_input)
        message = Message(
            message_type=MessageType.TEXT,
            text=text_message,
        )
    elif message_type == MessageType.AUDIO:
        encoded_audio_content = channel.get_audio(jb_channel, bot_input)
        audio_content = base64.b64decode(encoded_audio_content)
        audio_file_name = f"{turn_id}.ogg"
        storage = StorageHandler.get_async_instance()
        await storage.write_file(audio_file_name, audio_content, "audio/ogg")
        storage_url = await storage.public_url(audio_file_name)
        audio_message = AudioMessage(
            media_url=storage_url,
        )
        message = Message(
            message_type=MessageType.AUDIO,
            audio=audio_message,
        )
    elif message_type == MessageType.INTERACTIVE_REPLY:
        interactive_reply_message = channel.to_interactive_reply_message(bot_input)
        message = Message(
            message_type=MessageType.INTERACTIVE_REPLY,
            interactive_reply=interactive_reply_message,
        )
    elif message_type == MessageType.FORM_REPLY:
        form_reply_message = channel.to_form_reply_message(bot_input)
        message = Message(
            message_type=MessageType.FORM_REPLY,
            form_reply=form_reply_message,
        )
    elif message_type == MessageType.DIALOG:
        dialog_message = channel.to_dialog_message(bot_input)
        message = Message(
            message_type=MessageType.DIALOG,
            dialog=dialog_message,
        )
    else:
        channel_logger_object = await create_channel_logger_input(
            turn_id=turn_id, 
            channel_id=jb_channel.id, 
            channel_name=jb_channel.name, 
            message_type="Not Implemented", 
            sent_to_service = ""
        )
        return NotImplemented, channel_logger_object

    logger.info("Got a message: %s", message)
    if message:
        message_type = message.message_type
        if message_type == MessageType.TEXT or message_type == MessageType.AUDIO:
            language_input = Language(
                source="channel",
                turn_id=turn_id,
                intent=LanguageIntent.LANGUAGE_IN,
                message=message,
            )
            channel_logger_object = await create_channel_logger_input(
                turn_id=turn_id, 
                channel_id=jb_channel.id, 
                channel_name=jb_channel.name, 
                message_type=message.message_type.value, 
                sent_to_service = "Language"
            )
            return language_input, channel_logger_object
        else:
            if message_type == MessageType.DIALOG:
                flow_input = Flow(
                    source="channel",
                    intent=FlowIntent.DIALOG,
                    dialog=Dialog(turn_id=turn_id, message=message),
                )
            else:
                flow_input = Flow(
                    source="channel",
                    intent=FlowIntent.USER_INPUT,
                    user_input=UserInput(turn_id=turn_id, message=message),
                )
            channel_logger_object = await create_channel_logger_input(
                turn_id=turn_id, 
                channel_id=jb_channel.id, 
                channel_name=jb_channel.name, 
                message_type=message.message_type.value, 
                sent_to_service = "Flow"
            )
            return flow_input, channel_logger_object
