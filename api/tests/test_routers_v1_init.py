from io import BytesIO
from unittest import mock
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException, Request, UploadFile
import pytest
from app.jb_schema import JBBotActivate, JBBotChannels, JBBotCode
from lib.data_models.flow import Bot, BotConfig, BotIntent, Callback, CallbackType, Flow, FlowIntent
from lib.data_models.indexer import IndexType
from lib.models import JBBot, JBChannel, JBSession, JBUser

mock_extension = MagicMock()

@pytest.mark.asyncio
async def test_get_bots():
    mock_extension.reset_mock()

    mock_channel1 = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "active",
        name = "test_channel",
        type = "test_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )

    mock_channel2 = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id",
        status = "inactive",
        name = "test_channel",
        type = "test_type",
        key = "test_key",
        app_id = "12345678",
        url = "test_url",
    )
        
    mock_bot1 = JBBot(id="test_bot_1", name="Bot1", status="active", channels = [mock_channel1])
    mock_bot2 = JBBot(id="test_bot_2", name="Bot2", status="inactive", channels = [mock_channel2])

    bots = [mock_bot1,mock_bot2]

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import get_bots

        with patch("app.routers.v1.get_bot_list", return_value = bots) as mock_get_bot_list:
            result = await get_bots()

            assert isinstance(result,list)
            assert len(result) == len(bots)
            for item in result:
                assert isinstance(item, JBBot)
                assert item.status == item.channels[0].status
            assert result[0] == bots[0]
            assert result[1] == bots[1]

            mock_get_bot_list.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_secret_key():

    mock_extension.reset_mock()

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import get_secret_key

        result = await get_secret_key()

        assert len(result) == 1
        assert 'secret' in result
        assert result.get('secret') is not None

@pytest.mark.asyncio
async def test_refresh_secret_key():
    mock_extension.reset_mock()

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import refresh_secret_key

        result = await refresh_secret_key()

        assert len(result) == 1
        assert 'status' in result
        assert result.get('status') == 'success'

@pytest.mark.asyncio
async def test_install_bot_success():

    mock_extension.reset_mock()

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import install_bot
        from app.routers.v1 import KEYS
        mock_jbbot_code = JBBotCode(
            name = "Bot1",
            status = "active",
            dsl = "test_dsl",
            code = "test_code",
            requirements = "codaio",
            index_urls = ["index_url_1","index_url_2"],
            version = "1.0.0",
        )

        request = {
            "query_params": {
                "search": "fastapi",
                "page": "1"
            },
            "headers": {
                "authorization": f"Bearer {KEYS['JBMANAGER_KEY']}",
                "x-custom-header": "test_custom_value"
            },
            "user": "test_bot_user",
            "message_data":"test_data",
            "credentials" : {"key" : "test_key"}
        }

        mock_request = AsyncMock(Request)
        mock_request.json.return_value = request
        mock_request.headers = request["headers"]

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
                    required_credentials=mock_jbbot_code.required_credentials,
                    version=mock_jbbot_code.version,
                ),
            ),
        )
        with patch("app.routers.v1.handle_install_bot", return_value = mock_flow_input) as mock_handle_install_bot:
            result = await install_bot(mock_request, mock_jbbot_code)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            mock_handle_install_bot.assert_awaited_once_with(mock_jbbot_code)

@pytest.mark.asyncio
async def test_install_bot_failure_when_authorization_header_not_provided():

    mock_extension.reset_mock()

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import install_bot

        mock_jbbot_code = JBBotCode(
            name = "Bot1",
            status = "active",
            dsl = "test_dsl",
            code = "test_code",
            requirements = "codaio",
            index_urls = ["index_url_1","index_url_2"],
            version = "1.0.0",
        )

        request = {
            "query_params": {
                "search": "fastapi",
                "page": "1"
            },
            "headers": {
                "x-custom-header": "test_custom_value"
            },
            "user": "test_bot_user",
            "message_data":"test_data",
            "credentials" : {"key" : "test_key"}
        }

        mock_request = AsyncMock(Request)
        mock_request.json.return_value = request
        mock_request.headers = request["headers"]
        
        with pytest.raises(HTTPException) as exception_info:
            await install_bot(mock_request, mock_jbbot_code)

        assert exception_info.value.status_code == 401
        assert exception_info.value.detail == "Authorization header not provided"

@pytest.mark.asyncio
async def test_install_bot_failure_when_unauthorized():

    mock_extension.reset_mock()

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import install_bot

        mock_jbbot_code = JBBotCode(
            name = "Bot1",
            status = "active",
            dsl = "test_dsl",
            code = "test_code",
            requirements = "codaio",
            index_urls = ["index_url_1","index_url_2"],
            version = "1.0.0",
        )

        request = {
            "query_params": {
                "search": "fastapi",
                "page": "1"
            },
            "headers": {
                "authorization": "invalid_authorization",
                "x-custom-header": "test_custom_value"
            },
            "user": "test_bot_user",
            "message_data":"test_data",
            "credentials" : {"key" : "test_key"}
        }

        mock_request = AsyncMock(Request)
        mock_request.json.return_value = request
        mock_request.headers = request["headers"]
        
        with pytest.raises(HTTPException) as exception_info:
            await install_bot(mock_request, mock_jbbot_code)

        assert exception_info.value.status_code == 401
        assert exception_info.value.detail == "Unauthorized"

@pytest.mark.asyncio
async def test_activate_bot_success():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    request_body = JBBotActivate(
        phone_number = "919876543210",
        channels = JBBotChannels(
            whatsapp = "whatsapp"
        )
    )

    activate_bot_response = {"status": "success"}
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import activate_bot

        with patch("app.routers.v1.handle_activate_bot", return_value = activate_bot_response) as mock_handle_activate_bot:
            result = await activate_bot(bot_id, request_body)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            mock_handle_activate_bot.assert_awaited_once_with(bot_id=bot_id, request_body=request_body)

@pytest.mark.asyncio
async def test_activate_bot_failure_when_no_phone_number_provided():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    request_body = JBBotActivate(
        phone_number = "",
        channels = JBBotChannels(
            whatsapp = "whatsapp"
        )
    )

    activate_bot_response = {"status": "error", "message": "No phone number provided"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import activate_bot

        with patch("app.routers.v1.handle_activate_bot", return_value = activate_bot_response) as mock_handle_activate_bot:
            with pytest.raises(HTTPException) as exception_info:
                await activate_bot(bot_id, request_body)
            
            assert exception_info.value.status_code == 400
            assert exception_info.value.detail == activate_bot_response["message"]

            mock_handle_activate_bot.assert_awaited_once_with(bot_id=bot_id, request_body=request_body)

@pytest.mark.asyncio
async def test_get_bot_success():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"

    updated_info = {"status": "success", "message": "Bot deactivated"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import get_bot

        with patch("app.routers.v1.handle_deactivate_bot", return_value = updated_info) as mock_handle_deactivate_bot:
            result = await get_bot(bot_id)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            mock_handle_deactivate_bot.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_get_bot_failure():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"

    updated_info = {"status": "error", "message": "Bot not found"}
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import get_bot

        with patch("app.routers.v1.handle_deactivate_bot", return_value = updated_info) as mock_handle_deactivate_bot:
            with pytest.raises(HTTPException) as exception_info:
                await get_bot(bot_id)

            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == updated_info["message"]

            mock_handle_deactivate_bot.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_delete_bot_success():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"

    updated_info = {"status": "success", "message": "Bot deleted"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import delete_bot

        with patch("app.routers.v1.handle_delete_bot", return_value = updated_info) as mock_handle_delete_bot:
            result = await delete_bot(bot_id)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'
            mock_handle_delete_bot.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_delete_bot_failure():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"

    updated_info = {"status": "error", "message": "Bot not found"}
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import delete_bot

        with patch("app.routers.v1.handle_delete_bot", return_value = updated_info) as mock_handle_delete_bot:
            with pytest.raises(HTTPException) as exception_info:
                await delete_bot(bot_id)

            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == updated_info["message"]

            mock_handle_delete_bot.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_add_bot_configuraton_success():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    request = {
        "query_params": {
            "search": "fastapi",
            "page": "1"
        },
        "headers": {
            "authorization": "test_authorization",
            "x-custom-header": "test_custom_value"
        },
        "user": "test_bot_user",
        "message_data":"test_data",
        "credentials" : {"key" : "test_key"},
        "config_env" : {}
    }
    
    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request
    mock_request.credentials = request["credentials"]
    mock_request.config_env = request["config_env"]
    
    updated_info ={"status": "success", "message": "Bot updated", "bot":"sample_bot"}

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import add_bot_configuraton

        with patch("app.routers.v1.handle_update_bot", return_value = updated_info) as mock_handle_update_bot:
            result = await add_bot_configuraton(bot_id, mock_request)

            assert len(result) == 1
            assert 'status' in result
            assert result.get('status') == 'success'

            mock_handle_update_bot.assert_awaited_once()

@pytest.mark.asyncio
async def test_add_bot_configuraton_failure_when_no_credentials_and_no_config_env_provided():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    request = {
        "query_params": {
            "search": "fastapi",
            "page": "1"
        },
        "headers": {
            "authorization": "test_authorization",
            "x-custom-header": "test_custom_value"
        },
        "user": "test_bot_user",
        "message_data":"test_data",
    }
    
    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request
    
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import add_bot_configuraton

        with pytest.raises(HTTPException) as exception_info:
            await add_bot_configuraton(bot_id, mock_request)

        assert exception_info.value.status_code == 400
        assert exception_info.value.detail == "No credentials or config_env provided"

@pytest.mark.asyncio
async def test_add_bot_configuraton_failure_when_bot_not_found():

    mock_extension.reset_mock()

    bot_id = "invalid_bot_id"
    request = {
        "query_params": {
            "search": "fastapi",
            "page": "1"
        },
        "headers": {
            "authorization": "test_authorization",
            "x-custom-header": "test_custom_value"
        },
        "user": "test_bot_user",
        "message_data":"test_data",
        "credentials" : {"key" : "test_key"},
        "config_env" : {}
    }
    
    mock_request = AsyncMock(Request)
    mock_request.json.return_value = request
    mock_request.credentials = request["credentials"]
    mock_request.config_env = request["config_env"]
    
    updated_info = {"status": "error", "message": "Bot not found"}
    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import add_bot_configuraton

        with patch("app.routers.v1.handle_update_bot", return_value = updated_info) as mock_handle_update_bot:
            with pytest.raises(HTTPException) as exception_info:
                await add_bot_configuraton(bot_id, mock_request)

            assert exception_info.value.status_code == 404
            assert exception_info.value.detail == updated_info["message"]

            mock_handle_update_bot.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_session():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"
    session_id = "test_session_id"

    mock_chat_session1 = JBSession(id="test_session_id1", user_id="test_user_id1", channel_id="test_channel_id1")
    mock_chat_session2 = JBSession(id="test_session_id2", user_id="test_user_id2", channel_id="test_channel_id2")

    sessions = [mock_chat_session1,mock_chat_session2]

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import get_session

        with patch("app.routers.v1.get_bot_chat_sessions", return_value = sessions) as mock_get_bot_chat_sessions:
            result = await get_session(bot_id, session_id)

            assert isinstance(result,list)
            assert len(result) == len(sessions)
            for item in result:
                assert isinstance(item,JBSession)
                assert item in sessions

            mock_get_bot_chat_sessions.assert_awaited_once_with(bot_id, session_id)

@pytest.mark.asyncio
async def test_get_chats():

    mock_extension.reset_mock()

    bot_id = "test_bot_id"

    mock_session_object = JBSession(
        id = "test_session_id",
        user_id = "test_user_id",
        channel_id = "test_channel_id"
    )

    mock_user_object = JBUser(
        id = "test_user_id",
        channel_id = "test_channel_id",
        first_name = "test_first_name",
        last_name = "test_last_name",
        identifier = "test_identifier"
    )

    chats = [mock_session_object, mock_user_object]

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import get_chats

        with patch("app.routers.v1.get_chat_history", return_value = chats) as mock_get_chat_history:
            result = await get_chats(bot_id)

            assert isinstance(result,list)
            assert len(result) == len(chats)
            for item in result:
                assert isinstance(item,JBSession) or isinstance(item,JBUser)
                assert item in chats

            mock_get_chat_history.assert_awaited_once_with(bot_id)

@pytest.mark.asyncio
async def test_index_data():

    test_file_1 = UploadFile(filename="test_file_1.txt", file=BytesIO(b"test content for 1st file"))
    test_file_2 = UploadFile(filename="test_file_2.txt", file=BytesIO(b"test content for 2nd file"))

    indexer_type = IndexType.default
    collection_name = "test_collection"
    files = [test_file_1, test_file_2]
    indexing_chunk_size = 4000
    indexing_chunk_overlap_size = 200

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import index_data
        from lib.file_storage.handler import StorageHandler

        mock_storage_instance = MagicMock()
        
        with patch("app.routers.v1.StorageHandler.get_async_instance", return_value = mock_storage_instance):
            
            mock_storage_instance.write_file = AsyncMock()

            result = await index_data(indexer_type,collection_name, files, indexing_chunk_size, indexing_chunk_overlap_size)
            
            assert len(result) == 1
            assert 'message' in result
            assert result.get('message') == f"Indexing started for the files in {collection_name}"
            mock_storage_instance.write_file.assert_called()

@pytest.mark.asyncio
async def test_plugin_webhook_success():

    mock_extension.reset_mock()

    mock_webhook_data = b'{"data": "sample_body_data", "additional_field": "extra_value"}'
    mock_webhook_data_decoded = '{"data": "sample_body_data", "additional_field": "extra_value"}'

    mock_request = AsyncMock(Request)
    mock_request.body.return_value = mock_webhook_data

    flow_input = Flow(
        source="api",
        intent=FlowIntent.CALLBACK,
        callback=Callback(
            turn_id="test_turn_id",
            callback_type=CallbackType.EXTERNAL,
            external=mock_webhook_data,
        ),
    )

    async def mock_handle_webhook(mock_webhook_data_decoded):
        yield flow_input

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import plugin_webhook

        with patch("app.routers.v1.handle_webhook", mock_handle_webhook):

                result_status_code = await plugin_webhook(mock_request)

                assert result_status_code == 200

@pytest.mark.asyncio
async def test_plugin_webhook_failure():

    mock_extension.reset_mock()

    mock_webhook_data = b'{"data": "sample_body_data", "additional_field": "extra_value"}'
    mock_webhook_data_decoded = '{"data": "sample_body_data", "additional_field": "extra_value"}'

    mock_request = AsyncMock(Request)
    mock_request.body.return_value = mock_webhook_data

    flow_input = Flow(
        source="api",
        intent=FlowIntent.CALLBACK,
        callback=Callback(
            turn_id="test_turn_id",
            callback_type=CallbackType.EXTERNAL,
            external=mock_webhook_data,
        ),
    )

    async def mock_handle_webhook(mock_webhook_data_decoded):
        yield flow_input

    with patch.dict("sys.modules", {"app.extensions": mock_extension}):
        from app.routers.v1 import plugin_webhook

        with patch("app.routers.v1.handle_webhook", mock_handle_webhook):

                result_status_code = await plugin_webhook(mock_request)

                assert result_status_code == 200