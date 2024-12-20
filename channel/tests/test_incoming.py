import base64
from unittest.mock import patch, AsyncMock, MagicMock
import pytest

from lib.data_models import (
    Channel,
    MessageType,
    ChannelIntent,
    RestBotInput,
    Language,
    Flow,
    FlowIntent,
    LanguageIntent,
    DialogOption,
    Logger,
    ChannelLogger,
)
from lib.channel_handler import ChannelHandler
from src.handlers.incoming import process_incoming_messages


@pytest.fixture
def mock_async_storage_instance():
    async_storage_instance = MagicMock()
    mock_async_write_file = AsyncMock()
    mock_async_public_url = AsyncMock(return_value="https://storage.url/test_audio.ogg")

    async_storage_instance.write_file = mock_async_write_file
    async_storage_instance.public_url = mock_async_public_url
    return async_storage_instance


@pytest.fixture
def mock_get_channel_by_turn_id():
    return AsyncMock(return_value=MagicMock(channel_id="test_channel_id"))


def patch_all_channel_handler_get_audio_method(cls, method_name, return_value):
    """
    Patch the method `method_name` of all subclasses of `cls`.
    """
    patchers = []
    for subclass in cls.__subclasses__()[0].__subclasses__():
        patcher = patch.object(subclass, method_name, return_value=return_value)
        patchers.append(patcher)
    return patchers


@pytest.fixture
def patch_get_audio(request):
    patchers = patch_all_channel_handler_get_audio_method(
        ChannelHandler, "get_audio", base64.b64encode(b"audio_bytes")
    )
    for patcher in patchers:
        patcher.start()
        request.addfinalizer(patcher.stop)


text_inputs = {
    "pinnacle_whatsapp": RestBotInput(
        channel_name="pinnacle_whatsapp",
        headers={},
        query_params={},
        data={
            "timestamp": "1714990325",
            "text": {"body": "How are you?"},
            "type": "text",
        },
    ),
    "telegram": RestBotInput(
        channel_name="telegram",
        headers={},
        query_params={},
        data={"message_id": 1234, "date": 1721213755, "text": "How are you?"},
    ),
}

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bot_input", list(text_inputs.values()), ids=list(text_inputs.keys())
)
async def test_process_incoming_text_message(bot_input, mock_get_channel_by_turn_id):
    with patch(
        "src.handlers.incoming.get_channel_by_turn_id", mock_get_channel_by_turn_id
    ):
        message = Channel(
            source="api",
            turn_id="test_turn_id",
            intent=ChannelIntent.CHANNEL_IN,
            bot_input=bot_input,
        )
        channel_logger_object = Logger(
            source = "channel",
            logger_obj = ChannelLogger(
                id = "1234",
                turn_id = message.turn_id,
                channel_id =  "test_channel_id",
                channel_name = "telegram",
                msg_intent = "Incoming",
                msg_type = "text",
                sent_to_service = "Language",
                status = "Success/Failure"
            )
        )
        with patch('src.handlers.incoming.create_channel_logger_input',return_value=channel_logger_object):
            result, channel_logger_object = await process_incoming_messages(
                turn_id=message.turn_id, bot_input=bot_input
            )
            mock_get_channel_by_turn_id.assert_called_once_with("test_turn_id")

            assert result is not None
            assert isinstance(result, Language)
            assert result.turn_id == "test_turn_id"
            assert result.intent == LanguageIntent.LANGUAGE_IN
            assert result.message is not None
            assert result.message.message_type == MessageType.TEXT
            assert result.message.text is not None
            assert result.message.text.body == "How are you?"

audio_messages = {
    "pinnacle_whatsapp": RestBotInput(
        channel_name="pinnacle_whatsapp",
        headers={},
        query_params={},
        data={
            "timestamp": "1714990325",
            "audio": {
                "mime_type": "audio/ogg; codecs=opus",
                "sha256": "random_sha256_value",
                "id": "audio_id1",
                "voice": True,
            },
            "type": "audio",
        },
    ),
    "telegram": RestBotInput(
        channel_name="telegram",
        headers={},
        query_params={},
        data={
            "message_id": 1235,
            "date": 1721213963,
            "voice": {
                "duration": 2,
                "mime_type": "audio/ogg",
                "file_id": "test_file_id",
                "file_unique_id": "test_file_unique_id",
                "file_size": 45368,
            },
        },
    ),
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bot_input", list(audio_messages.values()), ids=list(audio_messages.keys())
)
async def test_process_incoming_audio_message(
    bot_input, mock_async_storage_instance, mock_get_channel_by_turn_id, patch_get_audio
):
    message = Channel(
        source="api",
        turn_id="test_turn_id",
        intent=ChannelIntent.CHANNEL_IN,
        bot_input=bot_input,
    )

    channel_logger_object = Logger(
        source = "channel",
        logger_obj = ChannelLogger(
            id = "1234",
            turn_id = message.turn_id,
            channel_id =  "test_channel_id",
            channel_name = "telegram",
            msg_intent = "Incoming",
            msg_type = "text",
            sent_to_service = "Language",
            status = "Success/Failure"
        )
    )

    with patch(
        "src.handlers.incoming.get_channel_by_turn_id", mock_get_channel_by_turn_id
    ):
        with patch(
            "lib.file_storage.StorageHandler.get_async_instance",
            return_value=mock_async_storage_instance,
        ), patch('src.handlers.incoming.create_channel_logger_input',return_value=channel_logger_object):
            result, channel_logger_object = await process_incoming_messages(
                turn_id=message.turn_id, bot_input=bot_input
            )
        mock_async_storage_instance.write_file.assert_called_once_with(
            "test_turn_id.ogg", b"audio_bytes", "audio/ogg"
        )
        mock_async_storage_instance.public_url.assert_called_once_with(
            "test_turn_id.ogg"
        )
        assert result is not None
        assert isinstance(result, Language)
        assert result.intent == LanguageIntent.LANGUAGE_IN
        assert result.message is not None
        assert result.message.message_type == MessageType.AUDIO
        assert result.message.audio is not None
        assert result.message.audio.media_url == "https://storage.url/test_audio.ogg"


interactive_messages = {
    "pinnacle_whatsapp": RestBotInput(
        channel_name="pinnacle_whatsapp",
        headers={},
        query_params={},
        data={
            "timestamp": "1714990452",
            "type": "interactive",
            "interactive": {
                "type": "button_reply",
                "button_reply": {"id": "option_id_1", "title": "option_id_1"},
            },
        },
    ),
    "telegram": RestBotInput(
        channel_name="telegram",
        headers={},
        query_params={},
        data={
            "id": "test_callback_id",
            "chat_instance": "-3027013130390797136",
            "data": "option_id_1",
        },
    ),
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bot_input",
    list(interactive_messages.values()),
    ids=list(interactive_messages.keys()),
)
async def test_process_incoming_interactive_message(
    bot_input, mock_get_channel_by_turn_id
):
    message = Channel(
        source="api",
        turn_id="test_turn_id",
        intent=ChannelIntent.CHANNEL_IN,
        bot_input=bot_input,
    )

    channel_logger_object = Logger(
        source = "channel",
            logger_obj = ChannelLogger(
            id = "1234",
            turn_id = message.turn_id,
            channel_id =  "test_channel_id",
            channel_name = "telegram",
            msg_intent = "Incoming",
            msg_type = "text",
            sent_to_service = "Language",
            status = "Success/Failure"
        )
    )
    
    with patch(
        "src.handlers.incoming.get_channel_by_turn_id", mock_get_channel_by_turn_id
    ), patch('src.handlers.incoming.create_channel_logger_input',return_value=channel_logger_object):
        result, channel_logger_object= await process_incoming_messages(
            turn_id=message.turn_id, bot_input=bot_input
        )
    assert result is not None
    assert isinstance(result, Flow)
    assert result.intent == FlowIntent.USER_INPUT
    assert result.user_input is not None
    assert result.user_input.turn_id == "test_turn_id"
    assert result.user_input.message is not None
    assert result.user_input.message.message_type == MessageType.INTERACTIVE_REPLY
    assert result.user_input.message.interactive_reply is not None
    assert result.user_input.message.interactive_reply.options is not None
    assert len(result.user_input.message.interactive_reply.options) == 1
    assert (
        result.user_input.message.interactive_reply.options[0].option_id
        == "option_id_1"
    )
    assert (
        result.user_input.message.interactive_reply.options[0].option_text
        == "option_id_1"
    )


language_selection_message = {
    "pinnacle_whatsapp": RestBotInput(
        channel_name="pinnacle_whatsapp",
        headers={},
        query_params={},
        data={
            "timestamp": "1714990499",
            "type": "interactive",
            "interactive": {
                "type": "list_reply",
                "list_reply": {
                    "id": "lang_english",
                    "title": "English",
                },
            },
        },
    ),
    "telegram": RestBotInput(
        channel_name="telegram",
        headers={},
        query_params={},
        data={
            "id": "test_callback_id",
            "chat_instance": "-3027013130390797136",
            "data": "lang_english",
        },
    ),
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bot_input",
    list(language_selection_message.values()),
    ids=list(language_selection_message.keys()),
)
async def test_process_incoming_language_selection_message(
    bot_input, mock_get_channel_by_turn_id
):
    message = Channel(
        source="api",
        turn_id="test_turn_id",
        intent=ChannelIntent.CHANNEL_IN,
        bot_input=bot_input,
    )

    channel_logger_object = Logger(
        source = "channel",
            logger_obj = ChannelLogger(
            id = "1234",
            turn_id = message.turn_id,
            channel_id =  "test_channel_id",
            channel_name = "telegram",
            msg_intent = "Incoming",
            msg_type = "text",
            sent_to_service = "Language",
            status = "Success/Failure"
        )
    )
    with patch(
        "src.handlers.incoming.get_channel_by_turn_id", mock_get_channel_by_turn_id
    ), patch('src.handlers.incoming.create_channel_logger_input',return_value=channel_logger_object):
        result, channel_logger_object = await process_incoming_messages(
            turn_id=message.turn_id, bot_input=bot_input
        )

    print(result)

    assert result is not None
    assert isinstance(result, Flow)
    assert result.intent == FlowIntent.DIALOG
    assert result.dialog is not None
    assert result.dialog.turn_id == "test_turn_id"
    assert result.dialog.message is not None
    assert result.dialog.message.message_type == MessageType.DIALOG
    assert result.dialog.message.dialog is not None
    assert result.dialog.message.dialog.dialog_id == DialogOption.LANGUAGE_SELECTED
    assert result.dialog.message.dialog.dialog_input == "en"


form_messages = {
    "pinnacle_whatsapp": RestBotInput(
        channel_name="pinnacle_whatsapp",
        headers={},
        query_params={},
        data={
            "timestamp": "1714990325",
            "type": "interactive",
            "interactive": {
                "type": "nfm_reply",
                "nfm_reply": {
                    "response_json": {"field": "value"},
                },
            },
        },
    )
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "bot_input", list(form_messages.values()), ids=list(form_messages.keys())
)
async def test_process_incoming_form_message(bot_input, mock_get_channel_by_turn_id):
    message = Channel(
        source="api",
        turn_id="test_turn_id",
        intent=ChannelIntent.CHANNEL_IN,
        bot_input=bot_input,
    )
    channel_logger_object = Logger(
        source = "channel",
            logger_obj = ChannelLogger(
            id = "1234",
            turn_id = message.turn_id,
            channel_id =  "test_channel_id",
            channel_name = "telegram",
            msg_intent = "Incoming",
            msg_type = "text",
            sent_to_service = "Language",
            status = "Success/Failure"
        )
    )
    with patch(
        "src.handlers.incoming.get_channel_by_turn_id", mock_get_channel_by_turn_id
    ), patch('src.handlers.incoming.create_channel_logger_input',return_value=channel_logger_object):
        result, channel_logger_object = await process_incoming_messages(
            turn_id=message.turn_id, bot_input=bot_input
        )
    assert result is not None
    assert isinstance(result, Flow)
    assert result.intent == FlowIntent.USER_INPUT
    assert result.user_input is not None
    assert result.user_input.turn_id == "test_turn_id"
    assert result.user_input.message is not None
    assert result.user_input.message.message_type == MessageType.FORM_REPLY
    assert result.user_input.message.form_reply is not None
    assert result.user_input.message.form_reply.form_data == {"field": "value"}
