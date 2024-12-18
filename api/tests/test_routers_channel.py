from fastapi import HTTPException, Request
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

mock_extension = MagicMock()

@pytest.mark.asyncio
async def test_get_all_channels():
    mock_extension.reset_mock()

    mock_channels_list = ["pinnacle_whatsapp","telegram","custom"]

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import get_all_channels

        with patch("app.routers.v2.channel.list_available_channels", return_value = mock_channels_list) as mock_list_available_channels:
            result = await get_all_channels()

            assert len(result) == len(mock_channels_list)
            for i in range(len(result)):
                assert result[i] == mock_channels_list[i]
            
            mock_list_available_channels.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_channel_success():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"

    request_body = {"key":"test_key", "app_id":"12345678", "name":"telegram", "type":"telegram", "url":"test_url"}
    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request_body
    
    updated_info = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import update_channel

        with patch("app.routers.v2.channel.update", return_value = updated_info) as mock_update:
            result = await update_channel(channel_id, mock_request)

            assert len(result) == 1
            assert len(result) == len(updated_info)
            assert 'status' in result
            assert result.get('status') == 'success'
            
            mock_update.assert_awaited_once_with(channel_id, request_body)

@pytest.mark.asyncio
async def test_update_channel_failure_when_channel_type_is_invalid():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"

    request_body = {"key":"test_key", "app_id":"12345678", "name":"test_name", "type":"test_type", "url":"test_url"}
    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request_body
    
    updated_info = {"status": "error", "message": "Channel not supported by this manager"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import update_channel

        with patch("app.routers.v2.channel.update", return_value = updated_info) as mock_update:
            with pytest.raises(HTTPException) as exception_info:
                await update_channel(channel_id, mock_request)
            
            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == updated_info["message"]

            mock_update.assert_awaited_once_with(channel_id, request_body)

@pytest.mark.asyncio
async def test_activate_channel_success():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"
    
    updated_info = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import activate_channel

        with patch("app.routers.v2.channel.activate", return_value = updated_info) as mock_activate:
            result = await activate_channel(channel_id)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            
            mock_activate.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_activate_channel_failure_when_channel_not_found():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"
    
    updated_info = {"status": "error", "message": "Channel not found"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import activate_channel

        with patch("app.routers.v2.channel.activate", return_value = updated_info) as mock_activate:
            with pytest.raises(HTTPException) as exception_info:
                await activate_channel(channel_id)
            
            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == updated_info["message"]

            mock_activate.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_deactivate_channel_success():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"
    
    updated_info = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import deactivate_channel

        with patch("app.routers.v2.channel.deactivate", return_value = updated_info) as mock_deactivate:
            result = await deactivate_channel(channel_id)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            
            mock_deactivate.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_deactivate_channel_failure_when_channel_not_found():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"
    
    updated_info = {"status": "error", "message": "Channel not found"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import deactivate_channel

        with patch("app.routers.v2.channel.deactivate", return_value = updated_info) as mock_deactivate:
            with pytest.raises(HTTPException) as exception_info:
                await deactivate_channel(channel_id)
            
            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == updated_info["message"]

            mock_deactivate.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_add_channel_success():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"
    
    delete_response = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import add_channel

        with patch("app.routers.v2.channel.delete", return_value = delete_response) as mock_delete:
            result = await add_channel(channel_id)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            
            mock_delete.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_add_channel_failure_when_channel_not_found():
    mock_extension.reset_mock()
    
    channel_id = "test_channel_id"
    
    delete_response = {"status": "error", "message": "Channel not found"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.channel import add_channel

        with patch("app.routers.v2.channel.delete", return_value = delete_response) as mock_delete:
            with pytest.raises(HTTPException) as exception_info:
                await add_channel(channel_id)
            
            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == delete_response["message"]

            mock_delete.assert_awaited_once_with(channel_id)
