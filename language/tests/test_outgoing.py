from typing import List
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from lib.data_models import (
    Channel,
    MessageType,
    LanguageIntent,
    Message,
    TextMessage,
    AudioMessage,
    ImageMessage,
    DocumentMessage,
    ButtonMessage,
    ListMessage,
    Option,
    Logger,
    LanguageLogger
)
from lib.model import LanguageCodes

mock_storage_instance = MagicMock()
mock_write_file = AsyncMock()
mock_public_url = AsyncMock(return_value="https://storage.url/test_audio.ogg")
mock_storage_instance.write_file = mock_write_file
mock_storage_instance.public_url = mock_public_url

mock_translator_instance = MagicMock()
mock_translate_text = AsyncMock(side_effect=lambda x, y, z: f"translated_{x}")
mock_translator_instance.translate_text = mock_translate_text

mock_speech_processor_instance = MagicMock()
mock_text_to_speech = AsyncMock(return_value=b"wav_data")
mock_speech_processor_instance.text_to_speech = mock_text_to_speech
mock_speech_to_text = AsyncMock(return_value="Vernacular text")
mock_speech_processor_instance.speech_to_text = mock_speech_to_text

mock_extension = MagicMock()
mock_extension.translator = mock_translator_instance
mock_extension.speech_processor = mock_speech_processor_instance
mock_extension.storage = mock_storage_instance

mock_convert_to_wav = AsyncMock(return_value=b"wav_data")

with patch.dict("sys.modules", {"src.extension": mock_extension}):
    with patch("src.audio_converter.convert_to_wav_with_ffmpeg", mock_convert_to_wav):
        import src.handlers

        handle_output = src.handlers.handle_output


@pytest.mark.asyncio
async def test_handle_output_text_message():
    mock_extension.reset_mock()
    turn_id = "turn1"
    preferred_language = LanguageCodes.EN
    message = Message(
        message_type=MessageType.TEXT,
        text=TextMessage(body="hello"),
    )

    language_logger_object = Logger(
        source = "language",
        logger_obj = LanguageLogger(
            id = "1234",
            turn_id = "turn1",
            msg_id = "abcd",
            msg_state = "Outgoing",
            msg_language = LanguageCodes.EN.value,
            msg_type = message.message_type.value,
            translated_to_language = preferred_language,
            translation_type = "Language translation/ Speech",
            translation_model = "Dhruva/Azure",
            response_time = "1.10235457",
            status = "Success"
        )
    )
    
    with patch.dict("sys.modules", {"src.extension": mock_extension}):
        with patch("src.handlers.create_language_logger_input", return_value = language_logger_object):
            result, language_logger_object_list = await handle_output(turn_id, preferred_language, message)

    assert isinstance(language_logger_object_list, list)
    assert len(language_logger_object_list) == 2
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Channel)
    assert result[0].turn_id == turn_id
    assert result[0].bot_output is not None
    assert result[0].bot_output.message_type == MessageType.TEXT
    assert result[0].bot_output.text is not None
    assert result[0].bot_output.text.body == "translated_hello"
    assert isinstance(result[1], Channel)
    assert result[1].turn_id == turn_id
    assert result[1].bot_output is not None
    assert result[1].bot_output.message_type == MessageType.AUDIO
    assert result[1].bot_output.audio is not None
    assert result[1].bot_output.audio.media_url == "https://storage.url/test_audio.ogg"


@pytest.mark.asyncio
async def test_handle_output_document_message():
    mock_extension.reset_mock()
    turn_id = "turn1"
    preferred_language = LanguageCodes.EN
    message = Message(
        message_type=MessageType.DOCUMENT,
        document=DocumentMessage(
            caption="doc_caption",
            url="http://example.com/doc.pdf",
            name="doc.pdf",
        ),
    )

    language_logger_object = Logger(
        source = "language",
        logger_obj = LanguageLogger(
            id = "1234",
            turn_id = "turn1",
            msg_id = "abcd",
            msg_state = "Outgoing/Coming from flow", 
            msg_language = LanguageCodes.EN.value,
            msg_type = message.message_type.value,
            translated_to_language = preferred_language,
            translation_type = "Text",
            translation_model = "Dhruva/Azure",
            response_time = "1.10235457",
            status = "Success"
        )
    )
    
    with patch.dict("sys.modules", {"src.extension": mock_extension}):
        with patch("src.handlers.create_language_logger_input", return_value = language_logger_object):
            result, language_logger_object_list = await handle_output(turn_id, preferred_language, message)

    assert isinstance(language_logger_object_list, list)
    assert len(language_logger_object_list) == 1
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Channel)
    assert result[0].turn_id == turn_id
    assert result[0].bot_output is not None
    assert result[0].bot_output.message_type == MessageType.DOCUMENT
    assert result[0].bot_output.document is not None
    assert result[0].bot_output.document.caption == "translated_doc_caption"
    assert result[0].bot_output.document.url == "http://example.com/doc.pdf"
    assert result[0].bot_output.document.name == "doc.pdf"


@pytest.mark.asyncio
async def test_handle_output_image_message():
    mock_extension.reset_mock()
    turn_id = "turn1"
    preferred_language = LanguageCodes.EN
    message = Message(
        message_type=MessageType.IMAGE,
        image=ImageMessage(
            caption="image_caption",
            url="http://example.com/image.jpg",
        ),
    )

    language_logger_object = Logger(
        source = "language",
        logger_obj = LanguageLogger(
            id = "1234",
            turn_id = "turn1",
            msg_id = "abcd",
            msg_state = "Outgoing/Text", 
            msg_language = "Preferred language" + LanguageCodes.EN.value,
            msg_type = "Image caption/Text",
            translated_to_language = preferred_language,
            translation_type = "Text",
            translation_model = "Dhruva/Azure",
            response_time = "1.10235457",
            status = "Success"
        )
    )
    
    with patch.dict("sys.modules", {"src.extension": mock_extension}):
        with patch("src.handlers.create_language_logger_input", return_value = language_logger_object):
            result, language_logger_object_list = await handle_output(turn_id, preferred_language, message)

    assert isinstance(language_logger_object_list, list)
    assert len(language_logger_object_list) == 1
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Channel)
    assert result[0].turn_id == turn_id
    assert result[0].bot_output is not None
    assert result[0].bot_output.message_type == MessageType.IMAGE
    assert result[0].bot_output.image is not None
    assert result[0].bot_output.image.caption == "translated_image_caption"
    assert result[0].bot_output.image.url == "http://example.com/image.jpg"


@pytest.mark.asyncio
async def test_handle_output_button_message():
    mock_extension.reset_mock()
    turn_id = "turn1"
    preferred_language = LanguageCodes.EN
    message = Message(
        message_type=MessageType.BUTTON,
        button=ButtonMessage(
            body="button_text",
            header="button_header",
            footer="button_footer",
            options=[
                Option(option_id="option_1", option_text="Option 1"),
                Option(option_id="option_2", option_text="Option 2"),
            ],
        ),
    )

    language_logger_object = Logger(
        source = "language",
        logger_obj = LanguageLogger(
            id = "1234",
            turn_id = "turn1",
            msg_id = "abcd",
            msg_state = "Outgoing", 
            msg_language = "Text/" + LanguageCodes.EN.value,
            msg_type = message.message_type.value,
            translated_to_language = preferred_language,
            translation_type = "Speech/" + message.message_type.value,
            translation_model = "Dhruva/Azure",
            response_time = "1.10235457",
            status = "Success"
        )
    )
    
    with patch.dict("sys.modules", {"src.extension": mock_extension}):
        with patch("src.handlers.create_language_logger_input", return_value = language_logger_object):
            result,language_logger_object_list = await handle_output(turn_id, preferred_language, message)

    assert isinstance(language_logger_object_list, list)
    assert len(language_logger_object_list) == 2
    assert isinstance(result, list)
    assert len(result) == 2
    assert isinstance(result[0], Channel)
    assert result[0].turn_id == turn_id
    assert result[0].bot_output is not None
    assert result[0].bot_output.message_type == MessageType.BUTTON
    assert result[0].bot_output.button is not None
    assert result[0].bot_output.button.body == "translated_button_text"
    assert result[0].bot_output.button.header == "translated_button_header"
    assert result[0].bot_output.button.footer == "translated_button_footer"
    assert len(result[0].bot_output.button.options) == 2
    assert result[0].bot_output.button.options[0].option_id == "option_1"
    assert result[0].bot_output.button.options[0].option_text == "translated_Option 1"
    assert result[0].bot_output.button.options[1].option_id == "option_2"
    assert result[0].bot_output.button.options[1].option_text == "translated_Option 2"
    assert isinstance(result[1], Channel)
    assert result[1].turn_id == turn_id
    assert result[1].bot_output is not None
    assert result[1].bot_output.message_type == MessageType.AUDIO
    assert result[1].bot_output.audio is not None
    assert result[1].bot_output.audio.media_url == "https://storage.url/test_audio.ogg"
