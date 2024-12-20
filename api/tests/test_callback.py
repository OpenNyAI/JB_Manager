from unittest.mock import patch, MagicMock
from typing import Dict
import pytest
from lib.data_models import (
    Channel,
    ChannelIntent,
    Logger,
    APILogger,
)

from lib.channel_handler import PinnacleWhatsappHandler
from app.handlers.v2.callback import handle_callback


@pytest.mark.asyncio
@patch("app.handlers.v2.callback.get_active_channel_by_identifier")
@patch("app.handlers.v2.callback.get_user_by_number")
@patch("app.handlers.v2.callback.create_user")
@patch("app.handlers.v2.callback.create_turn")
async def test_text_message(
    mock_create_turn,
    mock_create_user,
    mock_get_user_by_number,
    mock_get_active_channel_by_identifier,
):
    mock_get_active_channel_by_identifier.return_value = MagicMock(
        id="channel123", bot=MagicMock(id="bot123"), bot_id="bot123"
    )
    mock_get_user_by_number.return_value = None
    mock_create_user.return_value = MagicMock(id="user123")
    mock_create_turn.return_value = "turn123"

    callback_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "some_id",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919876543210",
                                "phone_number_id": "phone_no_id1",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "John Doe"},
                                    "wa_id": "919999999999",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919999999999",
                                    "id": "whatsapp_msg_id1",
                                    "timestamp": "1714990325",
                                    "text": {"body": "How are you?"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    result = [
        msg
        async for msg in handle_callback(
            "919876543210", callback_data, {}, {}, PinnacleWhatsappHandler
        )
    ]
    expected_message: Dict = callback_data["entry"][0]["changes"][0]["value"][
        "messages"
    ][0]
    expected_message.pop("context", None)
    expected_message.pop("from", None)
    expected_message.pop("id", None)

    # Assertions
    assert len(result) == 1
    logger_result = result[0][2]
    assert result[0][0] is None
    result = result[0][1]
    assert isinstance(result, Channel)
    assert result.turn_id == "turn123"
    assert result.intent == ChannelIntent.CHANNEL_IN
    assert result.bot_input is not None
    assert (
        result.bot_input.data
        == callback_data["entry"][0]["changes"][0]["value"]["messages"][0]
    )
    
    assert isinstance(logger_result, Logger)
    assert logger_result.source == "api"
    assert isinstance(logger_result.logger_obj, APILogger)
    assert logger_result.logger_obj.turn_id == "turn123"
    assert logger_result.logger_obj.user_id == "user123"

    mock_get_active_channel_by_identifier.assert_called_once_with(
        "919876543210", PinnacleWhatsappHandler.get_channel_name()
    )
    mock_get_user_by_number.assert_called_once_with(
        "919999999999", channel_id="channel123"
    )
    mock_create_user.assert_called_once_with(
        "channel123", "919999999999", "Dummy", "Dummy"
    )
    mock_create_turn.assert_called_once_with(
        bot_id="bot123",
        channel_id="channel123",
        user_id="user123",
    )


@pytest.mark.asyncio
@patch("app.handlers.v2.callback.get_active_channel_by_identifier")
@patch("app.handlers.v2.callback.get_user_by_number")
@patch("app.handlers.v2.callback.create_user")
@patch("app.handlers.v2.callback.create_turn")
async def test_audio_message(
    mock_create_turn,
    mock_create_user,
    mock_get_user_by_number,
    mock_get_active_channel_by_identifier,
):
    mock_get_active_channel_by_identifier.return_value = MagicMock(
        id="channel123", bot=MagicMock(id="bot123"), bot_id="bot123"
    )
    mock_get_user_by_number.return_value = None
    mock_create_user.return_value = MagicMock(id="user123")
    mock_create_turn.return_value = "turn123"

    callback_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "some_id_2",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919876543210",
                                "phone_number_id": "phone_no_id2",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "John Doe"},
                                    "wa_id": "919999999999",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "919999999999",
                                    "id": "whatsapp_msg_id2",
                                    "timestamp": "1714990407",
                                    "type": "audio",
                                    "audio": {
                                        "mime_type": "audio/ogg; codecs=opus",
                                        "sha256": "random_sha256_value",
                                        "id": "audio_id1",
                                        "voice": True,
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    result = [
        msg
        async for msg in handle_callback(
            "919876543210", callback_data, {}, {}, PinnacleWhatsappHandler
        )
    ]
    expected_message: Dict = callback_data["entry"][0]["changes"][0]["value"][
        "messages"
    ][0]
    expected_message.pop("from", None)
    expected_message.pop("id", None)

    # Assertions
    assert len(result) == 1
    logger_result = result[0][2]
    assert result[0][0] is None
    result = result[0][1]
    assert isinstance(result, Channel)
    assert result.turn_id == "turn123"
    assert result.intent == ChannelIntent.CHANNEL_IN
    assert result.bot_input is not None
    assert (
        result.bot_input.data
        == callback_data["entry"][0]["changes"][0]["value"]["messages"][0]
    )

    assert isinstance(logger_result, Logger)
    assert logger_result.source == "api"
    assert isinstance(logger_result.logger_obj, APILogger)
    assert logger_result.logger_obj.turn_id == "turn123"
    assert logger_result.logger_obj.user_id == "user123"

    mock_get_active_channel_by_identifier.assert_called_once_with(
        "919876543210", PinnacleWhatsappHandler.get_channel_name()
    )
    mock_get_user_by_number.assert_called_once_with(
        "919999999999", channel_id="channel123"
    )
    mock_create_user.assert_called_once_with(
        "channel123", "919999999999", "Dummy", "Dummy"
    )
    mock_create_turn.assert_called_once_with(
        bot_id="bot123",
        channel_id="channel123",
        user_id="user123",
    )


@pytest.mark.asyncio
@patch("app.handlers.v2.callback.get_active_channel_by_identifier")
@patch("app.handlers.v2.callback.get_user_by_number")
@patch("app.handlers.v2.callback.create_user")
@patch("app.handlers.v2.callback.create_turn")
async def test_button_reply_message(
    mock_create_turn,
    mock_create_user,
    mock_get_user_by_number,
    mock_get_active_channel_by_identifier,
):
    mock_get_active_channel_by_identifier.return_value = MagicMock(
        id="channel123", bot=MagicMock(id="bot123"), bot_id="bot123"
    )
    mock_get_user_by_number.return_value = None
    mock_create_user.return_value = MagicMock(id="user123")
    mock_create_turn.return_value = "turn123"

    callback_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "some_id3",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919876543210",
                                "phone_number_id": "phone_no_id3",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "John Doe"},
                                    "wa_id": "919999999999",
                                }
                            ],
                            "messages": [
                                {
                                    "context": {
                                        "from": "919876543210",
                                        "id": "whatsapp_user_id1",
                                    },
                                    "from": "919999999999",
                                    "id": "whatsapp_msg_id2",
                                    "timestamp": "1714990452",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "button_reply",
                                        "button_reply": {"id": "0", "title": "Yes"},
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    result = [
        msg
        async for msg in handle_callback(
            "919876543210", callback_data, {}, {}, PinnacleWhatsappHandler
        )
    ]
    expected_message: Dict = callback_data["entry"][0]["changes"][0]["value"][
        "messages"
    ][0]
    expected_message.pop("from", None)
    expected_message.pop("id", None)

    # Assertions
    assert len(result) == 1
    logger_result = result[0][2]
    assert result[0][0] is None
    result = result[0][1]
    assert isinstance(result, Channel)
    assert result.turn_id == "turn123"
    assert result.intent == ChannelIntent.CHANNEL_IN
    assert result.bot_input is not None
    assert (
        result.bot_input.data
        == callback_data["entry"][0]["changes"][0]["value"]["messages"][0]
    )

    assert isinstance(logger_result, Logger)
    assert logger_result.source == "api"
    assert isinstance(logger_result.logger_obj, APILogger)
    assert logger_result.logger_obj.turn_id == "turn123"
    assert logger_result.logger_obj.user_id == "user123"

    mock_get_active_channel_by_identifier.assert_called_once_with(
        "919876543210", PinnacleWhatsappHandler.get_channel_name()
    )
    mock_get_user_by_number.assert_called_once_with(
        "919999999999", channel_id="channel123"
    )
    mock_create_user.assert_called_once_with(
        "channel123", "919999999999", "Dummy", "Dummy"
    )
    mock_create_turn.assert_called_once_with(
        bot_id="bot123",
        channel_id="channel123",
        user_id="user123",
    )


@pytest.mark.asyncio
@patch("app.handlers.v2.callback.get_active_channel_by_identifier")
@patch("app.handlers.v2.callback.get_user_by_number")
@patch("app.handlers.v2.callback.create_user")
@patch("app.handlers.v2.callback.create_turn")
async def test_list_reply_message(
    mock_create_turn,
    mock_create_user,
    mock_get_user_by_number,
    mock_get_active_channel_by_identifier,
):
    mock_get_active_channel_by_identifier.return_value = MagicMock(
        id="channel123", bot=MagicMock(id="bot123"), bot_id="bot123"
    )
    mock_get_user_by_number.return_value = None
    mock_create_user.return_value = MagicMock(id="user123")
    mock_create_turn.return_value = "turn123"

    callback_data = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "some_id4",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "919876543210",
                                "phone_number_id": "phone_no_id4",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "John Doe"},
                                    "wa_id": "919999999999",
                                }
                            ],
                            "messages": [
                                {
                                    "context": {
                                        "from": "919876543210",
                                        "id": "whatsapp_user_id1",
                                    },
                                    "from": "919999999999",
                                    "id": "whatsapp_msg_id3",
                                    "timestamp": "1714990499",
                                    "type": "interactive",
                                    "interactive": {
                                        "type": "list_reply",
                                        "list_reply": {
                                            "id": "lang_english",
                                            "title": "English",
                                        },
                                    },
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    result = [
        msg
        async for msg in handle_callback(
            "919876543210", callback_data, {}, {}, PinnacleWhatsappHandler
        )
    ]
    expected_message: Dict = callback_data["entry"][0]["changes"][0]["value"][
        "messages"
    ][0]
    expected_message.pop("from", None)
    expected_message.pop("id", None)

    # Assertions
    assert len(result) == 1
    logger_result=result[0][2]
    assert result[0][0] is None
    result = result[0][1]
    assert isinstance(result, Channel)
    assert result.turn_id == "turn123"
    assert result.intent == ChannelIntent.CHANNEL_IN
    assert result.bot_input is not None
    assert (
        result.bot_input.data
        == callback_data["entry"][0]["changes"][0]["value"]["messages"][0]
    )

    assert isinstance(logger_result, Logger)
    assert logger_result.source == "api"
    assert isinstance(logger_result.logger_obj, APILogger)
    assert logger_result.logger_obj.turn_id == "turn123"
    assert logger_result.logger_obj.user_id == "user123"
    
    mock_get_active_channel_by_identifier.assert_called_once_with(
        "919876543210", PinnacleWhatsappHandler.get_channel_name()
    )
    mock_get_user_by_number.assert_called_once_with(
        "919999999999", channel_id="channel123"
    )
    mock_create_user.assert_called_once_with(
        "channel123", "919999999999", "Dummy", "Dummy"
    )
    mock_create_turn.assert_called_once_with(
        bot_id="bot123",
        channel_id="channel123",
        user_id="user123",
    )
