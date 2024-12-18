from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException, Request
import pytest
from unittest import mock
from lib.data_models.channel import Channel, ChannelIntent, RestBotInput
from lib.channel_handler.telegram_handler import TelegramHandler

mock_extension = MagicMock()

@pytest.mark.asyncio
async def test_callback_success():

    mock_extension.reset_mock()

    provider = "telegram"
    bot_identifier = "test_bot_identifier"

    mock_handler = mock.Mock(spec= TelegramHandler)
    mock_handler.get_channel_name.return_value = "telegram"
    mock_handler.is_valid_data.return_value = True 

    channel_map = {"telegram": mock_handler}

    request = {
        "query_params": {
            "search": "fastapi",
            "page": "1"
        },
        "headers": {
            "authorization": "test_token_value",
            "x-custom-header": "test_custom_value"
        },
        "user": "test_bot_user",
        "message_data":"test_data",
        "credentials" : {"key" : "test_key"}
    }

    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request
    mock_request.query_params = request["query_params"]
    mock_request.headers = request["headers"]
    
    mock_channel_input = Channel(
        source="api",
        turn_id="test_turn_id",
        intent=ChannelIntent.CHANNEL_IN,
        bot_input=RestBotInput(
            channel_name="telegram",
            headers=request.get("headers"),
            data={"message_data":"test_data"},
            query_params=request.get("query_params"),
        ),
    )
    mock_handle_callback = AsyncMock()
    mock_handle_callback.__aiter__.return_value = iter([(None, mock_channel_input)])

    with patch.dict("sys.modules", {"app.extensions": mock_extension}),\
        patch.dict("app.routers.v2.callback.channel_map", channel_map):

        from app.routers.v2.callback import callback

        with patch("app.routers.v2.callback.handle_callback") as mock_handle_callback:

            result_status_code = await callback(provider, bot_identifier, mock_request)

            assert result_status_code == 200
            mock_handle_callback.assert_called_once_with(bot_identifier=bot_identifier,
                                                         callback_data=request,
                                                         headers=request.get("headers"),
                                                         query_params=request.get("query_params"),
                                                         chosen_channel=mock_handler)
@pytest.mark.asyncio
async def test_callback_failure_when_no_valid_channel():
    mock_extension.reset_mock()

    provider = "invalid_channel"
    bot_identifier = "test_bot_identifier"

    mock_handler = mock.Mock(spec= TelegramHandler)
    mock_handler.get_channel_name.return_value = "telegram"
    mock_handler.is_valid_data.return_value = True 

    channel_map = {"telegram": mock_handler}

    request = {
        "query_params": {
            "search": "fastapi",
            "page": "1"
        },
        "headers": {
            "authorization": "test_token_value",
            "x-custom-header": "test_custom_value"
        },
        "user": "test_bot_user",
        "message_data":"test_data",
        "credentials" : {"key" : "test_key"}
    }

    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request
    mock_request.query_params = request["query_params"]
    mock_request.headers = request["headers"]
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}),\
        patch.dict("app.routers.v2.callback.channel_map", channel_map):

        from app.routers.v2.callback import callback

        result_status_code = await callback(provider, bot_identifier, mock_request)

        assert result_status_code == 404

@pytest.mark.asyncio
async def test_callback_failure_when_active_channel_not_found():
    mock_extension.reset_mock()

    provider = "telegram"
    bot_identifier = "test_bot_identifier"

    request = {
        "query_params": {},
        "headers": {},
        "user": "test_bot_user",
        "message_data":"test_data",
        "credentials" : {"key" : "test_key"}
    }

    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request
    mock_request.query_params = request["query_params"]
    mock_request.headers = request["headers"]
    
    mock_handler = mock.Mock(spec= TelegramHandler)
    mock_handler.get_channel_name.return_value = "telegram"
    mock_handler.is_valid_data.return_value = True 

    channel_map = {"telegram": mock_handler}

    async def mock_handle_callback(bot_identifier = bot_identifier,
                                   callback_data = request,
                                   headers= request["headers"],
                                   query_params= request["query_params"],
                                   chosen_channel= mock_handler,
                                   ):
        yield ValueError("Active channel not found"), None

    with patch.dict("sys.modules", {"app.extensions": mock_extension}), \
        patch.dict("app.routers.v2.callback.channel_map", channel_map):

        with patch("app.routers.v2.callback.handle_callback", mock_handle_callback):

            from app.routers.v2.callback import callback

            with pytest.raises(HTTPException) as exception_info:
                
                await callback(provider, bot_identifier, mock_request)

            assert exception_info.value.status_code == 400
            assert exception_info.value.detail == str(ValueError("Active channel not found"))