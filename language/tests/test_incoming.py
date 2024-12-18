from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from lib.data_models import (
    Flow,
    FlowIntent,
    MessageType,
    Message,
    TextMessage,
    AudioMessage,
)
from lib.model import LanguageCodes

mock_storage_instance = MagicMock()
mock_write_file = AsyncMock()
mock_public_url = AsyncMock(return_value="https://storage.url/test_audio.ogg")
mock_storage_instance.write_file = mock_write_file
mock_storage_instance.public_url = mock_public_url

mock_translator_instance = MagicMock()
mock_translate_text = AsyncMock()
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

        handle_input = src.handlers.handle_input


# Sample inputs for different message types
text_message = "Hello, this is a text message."
audio_url = "http://example.com/audio.mp3"
interactive_message = "This is an interactive message."


@pytest.mark.asyncio
async def test_handle_input_text_message():
    mock_extension.reset_mock()

    preferred_language = LanguageCodes.EN
    turn_id = "turn1"
    message = Message(
        message_type=MessageType.TEXT,
        text=TextMessage(body=text_message),
    )

    mock_translate_text.return_value = "Translated text message"

    result = await handle_input(turn_id, preferred_language, message)
    print(result)

    # Verifying the results
    mock_translate_text.assert_called_once_with(
        text_message, preferred_language, LanguageCodes.EN
    )

    assert result is not None
    assert isinstance(result, Flow)
    assert result.intent == FlowIntent.USER_INPUT
    assert result.user_input is not None
    assert result.user_input.turn_id == turn_id
    assert result.user_input.message is not None
    assert result.user_input.message.message_type == MessageType.TEXT
    assert result.user_input.message.text is not None
    assert result.user_input.message.text.body == "Translated text message"


@pytest.mark.asyncio
async def test_handle_input_audio_message():
    mock_extension.reset_mock()

    preferred_language = LanguageCodes.EN
    turn_id = "turn1"
    message = Message(
        message_type=MessageType.AUDIO,
        audio=AudioMessage(media_url=audio_url),
    )

    mock_speech_to_text.return_value = "Vernacular text"
    mock_translate_text.return_value = "Translated audio message"

    result = await handle_input(turn_id, preferred_language, message)

    # Verifying the results
    mock_convert_to_wav.assert_called_once_with(audio_url)
    mock_speech_to_text.assert_called_once_with(b"wav_data", preferred_language)
    mock_translate_text.assert_called_once_with(
        "Vernacular text", preferred_language, LanguageCodes.EN
    )
    assert result is not None
    assert isinstance(result, Flow)
    assert result.intent == FlowIntent.USER_INPUT
    assert result.user_input is not None
    assert result.user_input.turn_id == turn_id
    assert result.user_input.message is not None
    assert result.user_input.message.message_type == MessageType.TEXT
    assert result.user_input.message.text is not None
    assert result.user_input.message.text.body == "Translated audio message"

@pytest.mark.asyncio
async def test_handle_input_when_message_type_is_text_but_no_text_content_provided():
    mock_extension.reset_mock()

    preferred_language = LanguageCodes.EN
    turn_id = "turn1"

    message = MagicMock()
    message.message_type.return_value = MessageType.TEXT
    message.text.return_value = None

    with pytest.raises(ValueError) as exception_info:
        await handle_input(turn_id, preferred_language, message)
        
        assert exception_info.value == "Message text is empty"

@pytest.mark.asyncio
async def test_handle_input_when_message_type_is_audio_but_no_audio_content_provided():
    mock_extension.reset_mock()

    preferred_language = LanguageCodes.EN
    turn_id = "turn1"

    message = MagicMock()
    message.message_type.return_value = MessageType.AUDIO
    message.audio.return_value = None

    with pytest.raises(ValueError) as exception_info:
        await handle_input(turn_id, preferred_language, message)
        
        assert exception_info.value == "Message audio is empty"