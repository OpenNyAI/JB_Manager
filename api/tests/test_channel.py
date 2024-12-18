from unittest.mock import patch
import pytest
from app.handlers.v2.channel import list_available_channels, update, activate, deactivate, delete
from lib.channel_handler import channel_map
from lib.models import JBChannel

@pytest.mark.asyncio
async def test_list_available_channels():
    
    result = await list_available_channels()

    assert isinstance(result, list)
    assert result == list(channel_map.keys())

@pytest.mark.asyncio
async def test_update_failure_when_channel_not_found():

    channel_id = "test_channel_id"
    channel_data = {"key":"test_key", "app_id":"12345678", "name":"test_channel", "type":"test_channel_type", "url":"test_url"}

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = None) as mock_get_channel_by_id:
        result = await update(channel_id, channel_data)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Channel not found'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)
    
@pytest.mark.asyncio
async def test_update_failure_when_given_channel_type_not_supported_by_this_manager():

    channel_id = "test_channel_id"
    channel_data = {"key":"test_key", "app_id":"12345678", "name":"test_channel", "type":"test_channel_type", "url":"test_url"}

    mock_channel_object = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_channel_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = mock_channel_object) as mock_get_channel_by_id:
        result = await update(channel_id, channel_data)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Channel not supported by this manager'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_update_success():

    channel_id = "test_channel_id"
    channel_data = {"key":"test_key", "app_id":"12345678", "name":"telegram", "type":"telegram", "url":"test_url"}

    mock_channel_object = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "telegram",
        type = "telegram",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = mock_channel_object) as mock_get_channel_by_id, \
        patch("app.handlers.v2.channel.update_channel", return_value = channel_id) as mock_update_channel, \
        patch("app.handlers.v2.bot.EncryptionHandler.encrypt_text", return_value = "encrypted_test_key") as mock_encrypt_text:

        result = await update(channel_id, channel_data)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)
        mock_update_channel.assert_awaited_once()
        mock_encrypt_text.assert_called_once()

@pytest.mark.asyncio
async def test_activate_failure_when_channel_not_found():

    channel_id = "test_channel_id"

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = None) as mock_get_channel_by_id:
        result = await activate(channel_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Channel not found'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_activate_success():

    channel_id = "test_channel_id"
    channel_data = {"status": "active"}

    mock_channel_object = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "telegram",
        type = "telegram",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = mock_channel_object) as mock_get_channel_by_id, \
        patch("app.handlers.v2.channel.update_channel", return_value = channel_id) as mock_update_channel:

        result = await activate(channel_id)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)
        mock_update_channel.assert_awaited_once_with(channel_id, channel_data)

@pytest.mark.asyncio
async def test_deactivate_failure_when_channel_not_found():

    channel_id = "test_channel_id"

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = None) as mock_get_channel_by_id:
        result = await deactivate(channel_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Channel not found'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_deactivate_success():

    channel_id = "test_channel_id"
    channel_data = {"status": "inactive"}

    mock_channel_object = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "telegram",
        type = "telegram",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = mock_channel_object) as mock_get_channel_by_id, \
        patch("app.handlers.v2.channel.update_channel", return_value = channel_id) as mock_update_channel:

        result = await deactivate(channel_id)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)
        mock_update_channel.assert_awaited_once_with(channel_id, channel_data)

@pytest.mark.asyncio
async def test_delete_failure_when_channel_not_found():

    channel_id = "test_channel_id"

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = None) as mock_get_channel_by_id:
        result = await delete(channel_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Channel not found'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_delete_success():

    channel_id = "test_channel_id"
    channel_data = {"status": "deleted"}

    mock_channel_object = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "telegram",
        type = "telegram",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    with patch("app.handlers.v2.channel.get_channel_by_id", return_value = mock_channel_object) as mock_get_channel_by_id, \
        patch("app.handlers.v2.channel.update_channel", return_value = channel_id) as mock_update_channel:

        result = await delete(channel_id)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'
        
        mock_get_channel_by_id.assert_awaited_once_with(channel_id)
        mock_update_channel.assert_awaited_once_with(channel_id, channel_data)