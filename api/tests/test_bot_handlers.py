from unittest.mock import MagicMock, patch, Mock
import pytest
from app.jb_schema import JBBotCode
from app.handlers.v1.bot_handlers import handle_deactivate_bot, handle_delete_bot, handle_install_bot, handle_update_channel
from lib.data_models.flow import Bot, BotConfig, BotIntent, Flow, FlowIntent
from lib.models import JBBot, JBChannel

@pytest.mark.asyncio
async def test_handle_install_bot():
    
    mock_jbbot_code = JBBotCode(
        name = "Bot1",
        status = "active",
        dsl = "test_dsl",
        code = "test_code",
        requirements = "codaio",
        index_urls = ["index_url_1","index_url_2"],
        version = "1.0.0",
    )

    mock_bot_id = "test_bot_id"

    with patch("app.handlers.v1.bot_handlers.uuid.uuid4", return_value = mock_bot_id):
        result = await handle_install_bot(mock_jbbot_code)

        assert isinstance(result, Flow)
        assert result.source == "api"
        assert result.intent == FlowIntent.BOT
        assert isinstance(result.bot_config, BotConfig)
        assert result.bot_config.bot_id == mock_bot_id
        
        assert result.bot_config.bot_id == mock_bot_id
        assert result.bot_config.intent == BotIntent.INSTALL
        assert isinstance(result.bot_config.bot, Bot)
        assert result.bot_config.bot.name == mock_jbbot_code.name
        assert result.bot_config.bot.fsm_code== mock_jbbot_code.code
        assert result.bot_config.bot.requirements_txt == mock_jbbot_code.requirements
        assert result.bot_config.bot.index_urls == mock_jbbot_code.index_urls
        assert result.bot_config.bot.required_credentials == mock_jbbot_code.required_credentials
        assert result.bot_config.bot.version == mock_jbbot_code.version

@pytest.mark.asyncio
async def test_handle_update_channel_success():
    
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

    with patch("app.handlers.v1.bot_handlers.EncryptionHandler.encrypt_text", return_value = "encrypted_test_key") as mock_encrypt_text, \
        patch("app.handlers.v1.bot_handlers.get_channel_by_id", return_value = mock_channel_object) as mock_get_channel_by_id, \
            patch("app.handlers.v1.bot_handlers.update_channel", return_value = channel_id) as mock_update_channel:
        
        result = await handle_update_channel(channel_id, channel_data)

        assert len(result) == 3
        assert 'status' in result
        assert result.get('status') == 'success'
        assert 'message' in result
        assert result.get('message') == 'Channel updated'
        assert 'channel' in result
        assert isinstance(result.get('channel'),JBChannel)
        assert result.get('channel') == mock_channel_object

        mock_get_channel_by_id.assert_awaited_once_with(channel_id)
        mock_update_channel.assert_awaited_once()

@pytest.mark.asyncio
async def test_handle_update_channel_when_channel_not_found():
    
    channel_id = "test_channel_id"
    channel_data = {"key":"test_key", "app_id":"12345678", "name":"telegram", "type":"telegram", "url":"test_url"}

    with patch("app.handlers.v1.bot_handlers.EncryptionHandler.encrypt_text", return_value = "encrypted_test_key") as mock_encrypt_text, \
        patch("app.handlers.v1.bot_handlers.get_channel_by_id", return_value = None) as mock_get_channel_by_id:
        
        result = await handle_update_channel(channel_id, channel_data)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Channel not found'

        mock_get_channel_by_id.assert_awaited_once_with(channel_id)

@pytest.mark.asyncio
async def test_handle_delete_bot_success():
    
    channel_id = "test_channel_id"
    bot_id = "test_bot_id"
    bot_data = {"status": "deleted"}
    
    mock_channel = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )
    bot = JBBot(id="test_bot_id", name="Bot1", status="active", channels = [mock_channel])

    updated_info = {"status": "success", "message": "Bot updated", "bot": bot}
    
    with patch("app.handlers.v1.bot_handlers.handle_update_bot", return_value = updated_info) as mock_handle_update_bot, \
        patch("app.handlers.v1.bot_handlers.update_channel", return_value = channel_id) as mock_update_channel:
        
        result = await handle_delete_bot(bot_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'success' 
        assert 'message' in result
        assert result.get('message') == 'Bot deleted'

        mock_handle_update_bot.assert_awaited_once_with(bot_id, bot_data)
        mock_update_channel.assert_awaited_once()

@pytest.mark.asyncio
async def test_handle_delete_bot_when_bot_not_found():
    
    bot_id = "test_bot_id"
    bot_data = {"status": "deleted"}
    
    mock_channel = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    updated_info = {"status": "error", "message": "Bot not found"}
    
    with patch("app.handlers.v1.bot_handlers.handle_update_bot", return_value = updated_info) as mock_handle_update_bot:
        
        result = await handle_delete_bot(bot_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error' 
        assert 'message' in result
        assert result.get('message') == 'Bot not found'
        
        mock_handle_update_bot.assert_awaited_once_with(bot_id, bot_data)

@pytest.mark.asyncio
async def test_handle_deactivate_bot_success():
    
    channel_id = "test_channel_id"
    bot_id = "test_bot_id"
    
    mock_channel = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )
    bot = JBBot(id="test_bot_id", name="Bot1", status="active", channels = [mock_channel])

    with patch("app.handlers.v1.bot_handlers.get_bot_by_id", return_value = bot) as mock_get_bot_by_id, \
        patch("app.handlers.v1.bot_handlers.update_channel", return_value = channel_id) as mock_update_channel:
        
        result = await handle_deactivate_bot(bot_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'success' 
        assert 'message' in result
        assert result.get('message') == 'Bot deactivated'

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_update_channel.assert_awaited_once()

@pytest.mark.asyncio
async def test_handle_deactivate_bot_when_bot_not_found():
    
    bot_id = "test_bot_id"
    
    with patch("app.handlers.v1.bot_handlers.get_bot_by_id", return_value = None) as mock_get_bot_by_id:
        
        result = await handle_deactivate_bot(bot_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error' 
        assert 'message' in result
        assert result.get('message') == 'Bot not found'
        
        mock_get_bot_by_id.assert_awaited_once_with(bot_id)