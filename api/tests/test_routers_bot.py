from fastapi import HTTPException, Request
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from lib.data_models.flow import Bot, BotConfig, BotIntent, Flow, FlowIntent
from lib.models import JBBot
from app.jb_schema import JBBotCode, JBChannelContent

mock_extension = MagicMock()

@pytest.mark.asyncio
async def test_get_all_bots():
    
    mock_extension.reset_mock()

    mock_bot1 = JBBot(id = "test_bot_id1", name = "test_bot1", status = "active")
    mock_bot2 = JBBot(id = "test_bot_id2", name = "test_bot2", status = "inactive")

    mock_bot_list = [mock_bot1, mock_bot2]
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import get_all_bots
        
        with patch("app.routers.v2.bot.list_bots", return_value = mock_bot_list) as mock_list_bots:
            
            result = await get_all_bots()

            assert len(result) == len(mock_bot_list)
            for i in range(len(result)):
                assert result[i].id == mock_bot_list[i].id
                assert result[i].name == mock_bot_list[i].name
                assert result[i].status == mock_bot_list[i].status
            
            mock_list_bots.assert_awaited_once()

@pytest.mark.asyncio
async def test_install_bot_success():
    
    mock_extension.reset_mock()

    mock_jbbot_code = JBBotCode(
        name = "Bot1",
        status = "active",
        dsl = "test_dsl",
        code = "test_code",
        requirements = "codaio",
        index_urls = ["index_url_1","index_url_2"],
        version = "1.0.0",
    )

    mock_flow_input = Flow(
        source="api",
        intent=FlowIntent.BOT,
        bot_config=BotConfig(
            bot_id="test_bot_id",
            intent=BotIntent.INSTALL,
            bot=Bot(
                name=mock_jbbot_code.name,
                fsm_code=mock_jbbot_code.code,
                requirements_txt=mock_jbbot_code.requirements,
                index_urls=mock_jbbot_code.index_urls,
                version = "1.0.0"
            ),
        )
    )
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import install_bot
        
        with patch("app.routers.v2.bot.install", return_value = mock_flow_input) as mock_install:
            
            result = await install_bot(mock_jbbot_code)
            
            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'

            mock_install.assert_awaited_once_with(mock_jbbot_code)

@pytest.mark.asyncio
async def test_delete_bot_success():
    
    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    mock_delete_response = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import delete_bot
        
        with patch("app.routers.v2.bot.delete", return_value = mock_delete_response) as mock_delete:
            
            result = await delete_bot(bot_id)
            
            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'

            mock_delete.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_delete_bot_failure():
    
    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    mock_delete_response = {"status": "error", "message": "Bot not found"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import delete_bot
        
        with patch("app.routers.v2.bot.delete", return_value = mock_delete_response) as mock_delete:
            with pytest.raises(HTTPException) as exception_info:
                await delete_bot(bot_id)

            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == mock_delete_response["message"]
        
            mock_delete.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_add_bot_credentials_success():
    
    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    
    request = {
        "user": "test_bot_user",
        "credentials" : {"key" : "test_key"}
    }

    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request

    mock_add_credentials_response = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import add_bot_credentials
        
        with patch("app.routers.v2.bot.add_credentials", return_value = mock_add_credentials_response) as mock_add_credentials:
            
            result = await add_bot_credentials(bot_id, mock_request)
            
            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'

            mock_add_credentials.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_bot_credentials_failure_when_no_credentials_have_been_provided_in_request():
    
    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    request = {"user": "test_bot_user"}

    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import add_bot_credentials
        
        with pytest.raises(HTTPException) as exception_info:
            
            await add_bot_credentials(bot_id, mock_request)

        assert exception_info.value.status_code == 400
        assert exception_info.value.detail == "No credentials provided"

@pytest.mark.asyncio
async def test_add_bot_credentials_failure_when_no_bot_found_with_given_bot_id():
    
    mock_extension.reset_mock()

    bot_id = None
    request = {
        "user": "test_bot_user",
        "credentials" : {"key" : "test_key"}
    }

    mock_add_credentials_response = {"status": "error", "message": "Bot not found"}

    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import add_bot_credentials
        with patch("app.routers.v2.bot.add_credentials", return_value = mock_add_credentials_response) as mock_add_credentials:
            with pytest.raises(HTTPException) as exception_info:
                
                await add_bot_credentials(bot_id, mock_request)

            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == mock_add_credentials_response["message"]

            mock_add_credentials.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_bot_channel_success():
    
    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    channel_content = JBChannelContent(
        name = "telegram",
        type = "telegram",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )

    mock_add_channel_response = {"status": "success"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import add_bot_channel
        
        with patch("app.routers.v2.bot.add_channel", return_value = mock_add_channel_response) as mock_add_channel:
            
            result = await add_bot_channel(bot_id, channel_content)
            
            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'

            mock_add_channel.assert_awaited_once_with(bot_id, channel_content)

@pytest.mark.asyncio
async def test_add_bot_channel_failure_when_channel_not_supported_by_this_manager():
    
    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    channel_content = JBChannelContent(
        name = "test_name",
        type = "test_type",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v2.bot import add_bot_channel
        
        with pytest.raises(HTTPException) as exception_info:
            
            await add_bot_channel(bot_id, channel_content)

        assert exception_info.value.status_code == 400
        assert exception_info.value.detail == "Channel not supported by this manager"

@pytest.mark.asyncio
async def test_add_bot_channel_failure_when_bot_not_found():
    
    mock_extension.reset_mock()

    bot_id = None

    channel_content = JBChannelContent(
        name = "telegram",
        type = "telegram",
        url = "test_url",
        app_id = "12345678",
        key = "test_key",
        status = "active"
    )

    mock_add_channel_response = {"status": "error", "message": "Bot not found"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):

        from app.routers.v2.bot import add_bot_channel

        with patch("app.routers.v2.bot.add_channel", return_value = mock_add_channel_response) as mock_add_channel:
            with pytest.raises(HTTPException) as exception_info:
                
                await add_bot_channel(bot_id, channel_content)

                assert exception_info.value.status_code == 404
                assert exception_info.value.detail == mock_add_channel_response["message"]

                mock_add_channel.assert_awaited_once(bot_id, channel_content)