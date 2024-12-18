from unittest.mock import patch
import pytest
from lib.data_models import Flow, BotConfig, FlowIntent, Bot
from lib.models import JBBot, JBChannel
from app.handlers.v2.bot import list_bots, install, add_credentials, add_channel, delete
from app.jb_schema import JBBotCode, JBChannelContent

@pytest.mark.asyncio
async def test_list_bots():
    mock_bot1 = JBBot(id="test_bot_1", name="Bot1", status="active")
    mock_bot2 = JBBot(id="test_bot_2", name="Bot2", status="active")

    bot_list = [mock_bot1,mock_bot2]
    with patch("app.handlers.v2.bot.get_bot_list", return_value = bot_list) as mock_get_bot_list:
        result = await list_bots()

        assert result == bot_list
        mock_get_bot_list.assert_awaited_once()

@pytest.mark.asyncio
async def test_install():

    mock_jbbot_code = JBBotCode(
        name = "Bot1",
        status = "active",
        dsl = "test_dsl",
        code = "test_code",
        requirements = "codaio",
        index_urls = ["index_url_1","index_url_2"],
        version = "1.0.0",
    )

    mock_bot1 = JBBot(id="test_bot_1", 
                      name=mock_jbbot_code.name, 
                      status=mock_jbbot_code.status,
                      dsl = mock_jbbot_code.dsl, 
                      code = mock_jbbot_code.code, 
                      requirements = mock_jbbot_code.requirements, 
                      index_urls = mock_jbbot_code.index_urls, 
                      version = mock_jbbot_code.version)

    with patch("app.handlers.v2.bot.create_bot", return_value = mock_bot1) as mock_create_bot:
        result = await install(mock_jbbot_code)

        assert isinstance(result,Flow)
        assert result.source == "api"
        assert result.intent == FlowIntent.BOT
        assert isinstance(result.bot_config,BotConfig)
        assert result.bot_config.bot_id == mock_bot1.id
        assert isinstance(result.bot_config.bot,Bot)
        assert result.bot_config.bot.name == mock_jbbot_code.name
        assert result.bot_config.bot.fsm_code == mock_jbbot_code.code
        assert result.bot_config.bot.requirements_txt == mock_jbbot_code.requirements
        assert result.bot_config.bot.index_urls == mock_jbbot_code.index_urls
        assert result.bot_config.bot.version == mock_bot1.version
        
        mock_create_bot.assert_awaited_once_with(mock_jbbot_code.model_dump())
    
@pytest.mark.asyncio
async def test_add_credentials_success():
    bot_id = "test_bot_id"
    credentials = {"key":"test_key"}

    mock_bot = JBBot(id="test_bot_id", name="mock_bot", status="active")

    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = mock_bot) as mock_get_bot_by_id, \
        patch("app.handlers.v2.bot.update_bot", return_value = bot_id) as mock_update_bot, \
            patch("app.handlers.v2.bot.EncryptionHandler.encrypt_dict", return_value = "encrypted_test_key") as mock_encrypt_dict:

        result = await add_credentials(bot_id,credentials)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'
        
        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_update_bot.assert_awaited_once()
        mock_encrypt_dict.assert_called_once_with(credentials)

@pytest.mark.asyncio
async def test_add_credentials_failure():
    bot_id = "test_bot_id"
    credentials = {"key":"test_key"}

    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = None) as mock_get_bot_by_id, \
        patch("app.handlers.v2.bot.update_bot", return_value = bot_id) as mock_update_bot:

        result = await add_credentials(bot_id,credentials)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Bot not found'

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_update_bot.assert_not_awaited() 

@pytest.mark.asyncio
async def test_add_channel_when_bot_with_bot_id_does_not_exist():

    bot_id = "test_bot_id"

    channel_content = JBChannelContent(
        name = "test_channel_content",
        type = "test_type",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )

    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = None) as mock_get_bot_by_id:
        result = await add_channel(bot_id,channel_content)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == "Bot not found"

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        
@pytest.mark.asyncio
async def test_add_channel_when_channel_already_in_use_by_bot():

    bot_id = "test_bot_id"

    channel_content = JBChannelContent(
        name = "test_channel_content",
        type = "test_type",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )

    mock_bot = JBBot(id="test_bot_id", name="Bot1", status="active")

    mock_existing_channel = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
        bot = mock_bot
    )

    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = mock_bot) as mock_get_bot_by_id, \
        patch("app.handlers.v2.bot.get_active_channel_by_identifier", return_value = mock_existing_channel) as mock_get_active_channel_by_identifier:

        result = await add_channel(bot_id,channel_content)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == f"App ID {channel_content.app_id} already in use by bot {mock_existing_channel.bot.name}"

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_get_active_channel_by_identifier.assert_awaited_once_with(identifier = channel_content.app_id, 
                                                                       channel_type = channel_content.type)

@pytest.mark.asyncio
async def test_add_channel_when_bot_already_has_channel_of_given_type_for_given_app_id():

    bot_id = "test_bot_id"

    channel_content = JBChannelContent(
        name = "test_channel_content",
        type = "test_type",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )

    mock_bot = JBBot(
        id="test_bot_id", 
        name="Bot1", 
        status="active",
        channels = [JBChannel(
            id = "test_channel_id",
            bot_id = "test_bot_id",
            status = "active",
            name = "test_channel",
            type = "test_type",
            key = "test_key",
            app_id = "12345678",
            url = "test_url",
        )]
    )
            
    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = mock_bot) as mock_get_bot_by_id, \
        patch("app.handlers.v2.bot.get_active_channel_by_identifier", return_value = None) as mock_get_active_channel_by_identifier:

        result = await add_channel(bot_id,channel_content)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == f"Bot already has an channel of type {channel_content.type} for app ID {channel_content.app_id}"

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_get_active_channel_by_identifier.assert_awaited_once_with(identifier = channel_content.app_id, 
                                                                       channel_type = channel_content.type)

@pytest.mark.asyncio
async def test_add_channel_when_channel_creation_is_success():

    bot_id = "test_bot_id"

    channel_content = JBChannelContent(
        name = "test_channel_content",
        type = "test_type",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )

    mock_bot = JBBot(id="test_bot_id", name="Bot1", status="active")

    mock_channel = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_type",
        key = "encrypted_test_key",
        app_id = "12345678",
        url = "test_url"
    )

    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = mock_bot) as mock_get_bot_by_id, \
        patch("app.handlers.v2.bot.get_active_channel_by_identifier", return_value = None) as mock_get_active_channel_by_identifier, \
            patch("app.handlers.v2.bot.create_channel",return_value = mock_channel) as mock_create_channel, \
                patch("app.handlers.v2.bot.EncryptionHandler.encrypt_text", return_value = "encrypted_test_key") as mock_encrypt_text:

        result = await add_channel(bot_id,channel_content)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_get_active_channel_by_identifier.assert_awaited_once_with(identifier = channel_content.app_id, 
                                                                       channel_type = channel_content.type)
        mock_create_channel.assert_awaited_once_with(bot_id, channel_content.model_dump())
        mock_encrypt_text.assert_called_once()

@pytest.mark.asyncio
async def test_delete_success():

    bot_id = "test_bot_id"

    mock_bot = JBBot(id="test_bot_id", name="Bot1", status="active")

    bot_data = {"status": "deleted"}
    channel_data = {"status": "deleted"}

    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = mock_bot) as mock_get_bot_by_id, \
        patch("app.handlers.v2.bot.update_bot", return_value = bot_id) as mock_update_bot,\
            patch("app.handlers.v2.bot.update_channel_by_bot_id", return_value = bot_id) as mock_update_channel_by_bot_id:

        result = await delete(bot_id)

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)
        mock_update_bot.assert_awaited_once_with(bot_id, bot_data)
        mock_update_channel_by_bot_id.assert_awaited_once_with(bot_id, channel_data)

@pytest.mark.asyncio
async def test_delete_failure():

    bot_id = "test_bot_id"
    
    with patch("app.handlers.v2.bot.get_bot_by_id", return_value = None) as mock_get_bot_by_id:

        result = await delete(bot_id)

        assert len(result) == 2
        assert 'status' in result
        assert result.get('status') == 'error'
        assert 'message' in result
        assert result.get('message') == 'Bot not found'

        mock_get_bot_by_id.assert_awaited_once_with(bot_id)