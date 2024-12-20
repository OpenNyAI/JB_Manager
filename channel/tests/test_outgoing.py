from unittest.mock import patch, AsyncMock, MagicMock, Mock
import pytest

from lib.data_models import (
    MessageType,
    Message,
    TextMessage,
    AudioMessage,
    ButtonMessage,
    FormMessage,
    ImageMessage,
    DocumentMessage,
    DialogMessage,
    DialogOption,
    Option,
    Logger,
    ChannelLogger,
)

mock_async_storage_instance = MagicMock()
mock_async_write_file = AsyncMock()
mock_async_public_url = AsyncMock(return_value="https://storage.url/test_audio.ogg")

mock_async_storage_instance.write_file = mock_async_write_file
mock_async_storage_instance.public_url = mock_async_public_url

mock_sync_storage_instance = MagicMock()
mock_sync_write_file = MagicMock()
mock_sync_public_url = MagicMock(return_value="https://storage.url/test_audio.ogg")

mock_sync_storage_instance.write_file = mock_sync_write_file
mock_sync_storage_instance.public_url = mock_sync_public_url

mock_encryption_handler = MagicMock()
mock_encryption_handler.decrypt_dict = Mock(
    side_effect=lambda x: {
        k: v.replace("encrypted_", "decrypted_") for k, v in x.items()
    }
)
mock_encryption_handler.decrypt_text = Mock(
    side_effect=lambda x: x.replace("encrypted_", "decrypted_")
)

with patch(
    "lib.file_storage.StorageHandler.get_async_instance",
    return_value=mock_async_storage_instance,
):
    with patch(
        "lib.file_storage.StorageHandler.get_sync_instance",
        return_value=mock_sync_storage_instance,
    ):
        with patch("lib.encryption_handler.EncryptionHandler", mock_encryption_handler):
            import src.handlers.outgoing

            send_message_to_user = src.handlers.outgoing.send_message_to_user


test_messages = {
    "text_message": Message(
        message_type=MessageType.TEXT,
        text=TextMessage(
            body="Hello",
        ),
    ),
    "audio_message": Message(
        message_type=MessageType.AUDIO,
        audio=AudioMessage(
            media_url="https://example.com/audio.ogg",
        ),
    ),
    "button_message": Message(
        message_type=MessageType.BUTTON,
        button=ButtonMessage(
            body="This is a button message",
            header="Button header",
            footer="Button footer",
            options=[
                Option(option_id="1", option_text="Option 1"),
                Option(option_id="2", option_text="Option 2"),
            ],
        ),
    ),
    "image_message": Message(
        message_type=MessageType.IMAGE,
        image=ImageMessage(
            url="https://example.com/image.jpg",
            caption="This is an image",
        ),
    ),
    "document_message": Message(
        message_type=MessageType.DOCUMENT,
        document=DocumentMessage(
            url="https://example.com/document.pdf",
            name="Document title",
            caption="This is a document",
        ),
    ),
    "form_message": Message(
        message_type=MessageType.FORM,
        form=FormMessage(
            header="Form header",
            body="Form body",
            footer="Form footer",
            form_id="form_id",
        ),
    ),
    "language_message": Message(
        message_type=MessageType.DIALOG,
        dialog=DialogMessage(
            dialog_id=DialogOption.LANGUAGE_CHANGE,
            dialog_input=None,
        ),
    ),
}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "message",
    list(test_messages.values()),
    ids=list(test_messages.keys()),
)
async def test_send_message_to_user(message):
    mock_channel = MagicMock(
        app_id="test_number",
        key="encrypted_credentials",
        type="pinnacle_whatsapp",
        url="https://api.pinnacle.com",
    )
    mock_user = MagicMock(
        identifier="1234567890",
    )
    mock_get_user_by_turn_id = AsyncMock(return_value=mock_user)
    mock_get_channel_by_turn_id = AsyncMock(return_value=mock_channel)
    mock_send_message = MagicMock()
    mock_create_message = AsyncMock()

    turn_id = "test_turn_id"

    with patch("src.handlers.outgoing.get_user_by_turn_id", mock_get_user_by_turn_id):
        with patch(
            "src.handlers.outgoing.get_channel_by_turn_id", mock_get_channel_by_turn_id
        ):
            with patch(
                "lib.channel_handler.pinnacle_whatsapp_handler.PinnacleWhatsappHandler.send_message",
                mock_send_message,
            ):
                with patch("src.handlers.outgoing.create_message", mock_create_message):
                    channel_logger_object = await send_message_to_user(turn_id=turn_id, message=message)
  
    mock_get_channel_by_turn_id.assert_called_once_with(turn_id=turn_id)
    mock_get_user_by_turn_id.assert_called_once_with(turn_id=turn_id)
    mock_send_message.assert_called_once_with(
        channel=mock_channel, user=mock_user, message=message
    )
    mock_create_message.assert_called_once()

    print("Channel logger object:", channel_logger_object)
    assert isinstance(channel_logger_object, Logger)
    assert isinstance(channel_logger_object.logger_obj,ChannelLogger)
    assert channel_logger_object.logger_obj.turn_id == turn_id
    assert channel_logger_object.logger_obj.msg_type == message.message_type.value