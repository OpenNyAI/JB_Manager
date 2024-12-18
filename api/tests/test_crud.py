import pytest
from unittest import mock
from uuid import uuid4
from lib.db_session_handler import DBSessionHandler
from lib.models import JBUser, JBChannel, JBBot, JBWebhookReference, JBSession
from app.crud import (
    create_user, 
    create_turn, 
    get_user_by_number, 
    get_channel_by_id, 
    get_bot_list, 
    get_channels_by_identifier, 
    update_bot,
    update_channel,
    update_channel_by_bot_id,
    get_bot_by_id,
    get_plugin_reference,
    get_bot_chat_sessions,
    create_bot,
    create_channel,
    get_active_channel_by_identifier,
    get_chat_history
)

class AsyncContextManagerMock:
    def __init__(self, session_mock):
        self.session_mock = session_mock

    async def __aenter__(self): 
        return self.session_mock
    
    async def __aexit__(self, exc_type, exc_val, exc_tb): 
        pass

class AsyncBeginMock:
    async def __aenter__(self):
        pass  
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  

@pytest.mark.asyncio
async def test_create_user_success():
    channel_id = "channel123"
    phone_number = "1234567890"
    first_name = "John"
    last_name = "Doe"

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        user = await create_user(channel_id, phone_number, first_name, last_name)
        
        assert user is not None
        assert user.first_name == first_name
        assert user.last_name == last_name
        assert user.identifier == phone_number
        assert user.channel_id == channel_id
        assert isinstance(user.id, str)  
        assert len(user.id) == 36  

        mock_session.commit.assert_awaited_once()
            
@pytest.mark.asyncio
async def test_create_user_db_failure():
    channel_id = "channel123"
    phone_number = "1234567890"
    first_name = "John"
    last_name = "Doe"

    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await create_user(channel_id, phone_number, first_name, last_name)

@pytest.mark.asyncio
async def test_create_turn_success():
    bot_id = "test_bot_id"
    channel_id = "channel123"
    user_id = "test_user_id"

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        turn_id = await create_turn(bot_id, channel_id, user_id)
    
        assert turn_id is not None
        assert isinstance(turn_id, str) 
        assert len(turn_id) == 36  

        mock_session.commit.assert_awaited_once()
            
@pytest.mark.asyncio
async def test_create_turn_db_failure():
    
    bot_id = "test_bot_id"
    channel_id = "channel123"
    user_id = "test_user_id"

    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await create_turn(bot_id, channel_id, user_id)

@pytest.mark.asyncio
async def test_get_user_by_number_success():
    phone_number = "1234567890"
    channel_id = "channel123"
    
    mock_user = JBUser(
        id=str(uuid4()), 
        channel_id=channel_id, 
        first_name="John", 
        last_name="Doe", 
        identifier=phone_number
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_user 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_user_by_number(phone_number, channel_id)

        assert result.id == mock_user.id
        assert result.channel_id == mock_user.channel_id
        assert result.first_name == mock_user.first_name
        assert result.last_name == mock_user.last_name
        assert result.identifier == mock_user.identifier
        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_user_by_number_failure():
    phone_number = "1234567890"
    channel_id = "channel123"
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await get_user_by_number(phone_number, channel_id)

@pytest.mark.asyncio
async def test_get_channel_by_id_success():
    channel_id = "channel123"
    
    mock_channel = JBChannel(
        id = channel_id,
        bot_id = "test_bot_id",
        status = "active",
        name = "telegram",
        type = "telegram",
        key = "mfvghsikzhfcdfhjsrghehssliakzjfhsk"
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_channel 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_channel_by_id(channel_id)

        assert result.id == mock_channel.id
        assert result.bot_id == mock_channel.bot_id
        assert result.status == mock_channel.status
        assert result.name == mock_channel.name
        assert result.type == mock_channel.type
        assert result.key == mock_channel.key

        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_channel_by_id_failure():
    channel_id = "channel123"
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await get_channel_by_id(channel_id)

@pytest.mark.asyncio
async def test_get_bot_list_success():
    mock_bot1 = JBBot(id=1, name="Bot1", status="active")
    mock_bot2 = JBBot(id=2, name="Bot2", status="active")
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_execute_result = mock.Mock()
    
    mock_scalars = mock.Mock()
    mock_scalars.unique.return_value = mock_scalars  
    mock_scalars.all.return_value = [mock_bot1, mock_bot2] 
    
    mock_execute_result.scalars.return_value = mock_scalars
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        bot_list = await get_bot_list()
        assert bot_list == [mock_bot1, mock_bot2]
        mock_session.execute.assert_awaited_once() 


@pytest.mark.asyncio
async def test_get_bot_list_no_bots_found():

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock()) 
    mock_execute_result = mock.Mock()
    
    mock_scalars = mock.Mock()
    mock_scalars.unique.return_value = mock_scalars 
    mock_scalars.all.return_value = []
    
    mock_execute_result.scalars.return_value = mock_scalars
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        bot_list = await get_bot_list()
        assert bot_list == []
        mock_session.execute.assert_awaited_once()  

@pytest.mark.asyncio
async def test_get_channels_by_identifier_success():
    identifier = "1234567890"
    channel_type = "telegram"

    mock_channel1 = JBChannel(app_id="1234567890", type="telegram", status="inactive")
    mock_channel2 = JBChannel(app_id="1234567890", type="telegram", status="active")
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_execute_result = mock.Mock()
    
    mock_scalars = mock.Mock()
    mock_scalars.unique.return_value = mock_scalars  
    mock_scalars.all.return_value = [mock_channel1, mock_channel2] 
    
    mock_execute_result.scalars.return_value = mock_scalars
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        channels_list = await get_channels_by_identifier(identifier, channel_type) 
        assert channels_list == [mock_channel1, mock_channel2] 
        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_channels_by_identifier_no_channels_found():

    identifier = "1234567890"
    channel_type = "telegram"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock()) 
    mock_execute_result = mock.Mock()
    
    mock_scalars = mock.Mock()
    mock_scalars.unique.return_value = mock_scalars 
    mock_scalars.all.return_value = []
    
    mock_execute_result.scalars.return_value = mock_scalars
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        channels_list = await get_channels_by_identifier(identifier, channel_type)
        assert channels_list == []
        mock_session.execute.assert_awaited_once()  

@pytest.mark.asyncio
async def test_update_bot_success():
    bot_id = "test_bot_id"
    data = {"status":"active"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_execute.return_value.rowcount = 1
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        
        result = await update_bot(bot_id, data)
        assert result is not None
        assert result == bot_id

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_bot_no_bot_found():
    bot_id = None
    data = {"status":"active"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 

    mock_execute = mock.AsyncMock()
    mock_execute.return_value.rowcount = 0
    mock_session.execute = mock_execute 

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await update_bot(bot_id, data)
        assert result is None

        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once() 

@pytest.mark.asyncio
async def test_update_bot_error():

    bot_id = "test_bot_id"
    data = {"status":"deleted"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock(side_effect=Exception("Database error"))
    mock_session.execute = mock_execute  
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with pytest.raises(Exception, match="Database error"):
            await update_bot(bot_id, data)
        
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_update_channel_success():
    channel_id = "test_channel_id"
    data = {"status": "active", "key": "ahjbdbhsbdrhiiuciuhrqtnjuifh"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_execute.return_value.rowcount = 1
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await update_channel(channel_id, data)
        assert result is not None
        assert result == channel_id

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_channel_no_channel_found():
    channel_id = None
    data = {"status": "active", "key": "ahjbdbhsbdrhiiuciuhrqtnjuifh"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 

    mock_execute = mock.AsyncMock()
    mock_execute.return_value.rowcount = 0
    mock_session.execute = mock_execute 

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await update_channel(channel_id, data)
        assert result is None

        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once() 

@pytest.mark.asyncio
async def test_update_channel_error():
    channel_id = "test_channel_id"
    data = {"status": "active", "key": "ahjbdbhsbdrhiiuciuhrqtnjuifh"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock(side_effect=Exception("Database error"))
    mock_session.execute = mock_execute  
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with pytest.raises(Exception, match="Database error"):
            await update_channel(channel_id, data)
        
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_update_channel_by_bot_id_success():
    bot_id = "test_bot_id"
    data = {"status": "deleted"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_execute.return_value.rowcount = 1
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await update_channel_by_bot_id(bot_id, data)
        assert result is not None
        assert result == bot_id

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_channel_by_bot_id_no_channel_found():
    bot_id = None
    data = {"status": "deleted"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 

    mock_execute = mock.AsyncMock()
    mock_execute.return_value.rowcount = 0
    mock_session.execute = mock_execute 

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await update_channel_by_bot_id(bot_id, data)
        assert result is None

        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once() 

@pytest.mark.asyncio
async def test_update_channel_by_bot_id_error():
    bot_id = "test_bot_id"
    data = {"status": "deleted"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock(side_effect=Exception("Database error"))
    mock_session.execute = mock_execute  
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with pytest.raises(Exception, match="Database error"):
            await update_channel_by_bot_id(bot_id, data)
        
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_bot_by_id_success():
    bot_id = "test_bot_id"
    
    mock_bot = JBBot(
        id = "test_bot_id",
        name = "My_Bot",
        status = "active",
        dsl = "test_dsl",
        code = "test_code",
        requirements = "codaio",
        index_urls = ["index-url1","index_url2"],
        required_credentials = ["OPEN_API_KEY", "CODAIO"],
        version = "1.0.0"
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.unique.return_value.first.return_value = mock_bot 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_bot_by_id(bot_id)

        assert isinstance(result, JBBot)
        assert result.id == mock_bot.id
        assert result.name == mock_bot.name
        assert result.status == mock_bot.status
        assert result.dsl == mock_bot.dsl
        assert result.code == mock_bot.code
        assert result.requirements == mock_bot.requirements
        assert result.index_urls == mock_bot.index_urls
        assert result.required_credentials == mock_bot.required_credentials
        assert result.version == mock_bot.version

        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_bot_by_id_failure():
    bot_id = "test_bot_id"
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await get_bot_by_id(bot_id)

@pytest.mark.asyncio
async def test_get_plugin_reference_success():
    plugin_uuid = "test_id"
    
    mock_webhook_reference = JBWebhookReference(
        id = "test_id",
        turn_id = "test_turn_id"
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_webhook_reference 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_plugin_reference(plugin_uuid)

        assert isinstance(result, JBWebhookReference)
        assert result.id == mock_webhook_reference.id
        assert result.turn_id == mock_webhook_reference.turn_id

        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_plugin_reference_failure():
    plugin_uuid = "test_id"
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await get_plugin_reference(plugin_uuid)

@pytest.mark.asyncio
async def test_get_bot_chat_sessions_success():

    bot_id = "test_bot_id"
    session_id = "test_session_id"
    
    mock_chat_session1 = JBSession(id="test_session_id", user_id="test_user_id1", channel_id="test_channel_id1")

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_execute_result = mock.Mock()
    
    mock_execute_result.unique.return_value.scalars.return_value.all.return_value = [mock_chat_session1] 

    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result_chat_sessions = await get_bot_chat_sessions (bot_id, session_id)

        assert len(result_chat_sessions) == 1
        assert result_chat_sessions[0].id == mock_chat_session1.id
        assert result_chat_sessions[0].user_id == mock_chat_session1.user_id
        assert result_chat_sessions[0].channel_id == mock_chat_session1.channel_id

        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_bot_chat_sessions_failure_no_chat_sessions_found():

    bot_id = "test_bot_id"
    session_id = "test_session_id"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_execute_result = mock.Mock()
    
    mock_execute_result.unique.return_value.scalars.return_value.all.return_value = [] 

    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result_chat_sessions = await get_bot_chat_sessions (bot_id, session_id)
        assert result_chat_sessions == []
        mock_session.execute.assert_awaited_once()  

@pytest.mark.asyncio
async def test_create_bot_success():
    
    data = {'name': 'Bot1', 'status': 'active', 'dsl': 'test_dsl', 'code': 'test_code', 'requirements': 'codaio',
            'index_urls': ['index_url_1', 'index_url_2'], 'required_credentials':['OPEN_API_KEY'], 'version': '1.0.0'}

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        bot = await create_bot(data)
        
        assert bot is not None
        assert isinstance(bot, JBBot)  
        assert isinstance(bot.id,str)
        assert len(bot.id) == 36  
        assert bot.name == data.get('name')
        assert bot.dsl == data.get('dsl')
        assert bot.code == data.get('code')
        assert bot.requirements == data.get('requirements')
        assert bot.index_urls == data.get('index_urls')
        assert bot.required_credentials == data.get('required_credentials')
        assert bot.version == data.get('version')

        mock_session.commit.assert_awaited_once()
            
@pytest.mark.asyncio
async def test_create_bot_failure():

    data = {'name': 'Bot1', 'status': 'active', 'dsl': 'test_dsl', 'code': 'test_code', 'requirements': 'codaio',
            'index_urls': ['index_url_1', 'index_url_2'], 'required_credentials':['OPEN_API_KEY'], 'version': '1.0.0'}

    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await create_bot(data)

@pytest.mark.asyncio
async def test_create_channel_success():
    
    bot_id = "test_bot_id"
    data = {'name': 'telegram', 'type': 'telegram', 'key': 'test_key', 'app_id': 'test_app_id', 'url': 'test_url','status': 'active'}

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        channel = await create_channel(bot_id, data)
        
        assert channel is not None
        assert isinstance(channel, JBChannel)  
        assert isinstance(channel.id,str)
        assert len(channel.id) == 36  
        assert channel.bot_id == bot_id
        assert channel.name == data.get('name')
        assert channel.type == data.get('type')
        assert channel.key == data.get('key')
        assert channel.app_id == data.get('app_id')
        assert channel.url == data.get('url')
        assert channel.status == data.get('status')

        mock_session.commit.assert_awaited_once()
            
@pytest.mark.asyncio
async def test_create_channel_failure():

    bot_id = "test_bot_id"
    data = {'name': 'telegram', 'type': 'telegram', 'key': 'test_key', 'app_id': 'test_app_id', 'url': 'test_url','status': 'active'}

    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await create_channel(bot_id, data)

@pytest.mark.asyncio
async def test_get_active_channel_by_identifier_success():

    identifier = "test_app_id"
    channel_type = "telegram"
    
    mock_channel = JBChannel(
        id = "test_channel_id",
        bot_id = "test_bot_id" ,
        status = "active",
        name = "telegram",
        type = "telegram",
        key = "test_key",
        app_id = "test_app_id",
        url = "test_url"
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.unique.return_value.first.return_value = mock_channel 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_active_channel_by_identifier(identifier, channel_type)

        assert result is not None
        assert isinstance(result, JBChannel)
        assert result.id == mock_channel.id
        assert result.bot_id == mock_channel.bot_id
        assert result.status == mock_channel.status
        assert result.name == mock_channel.name
        assert result.type == mock_channel.type
        assert result.key == mock_channel.key
        assert result.app_id == mock_channel.app_id
        assert result.url == mock_channel.url

        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_get_active_channel_by_identifier_failure():

    identifier = "test_app_id"
    channel_type = "telegram"
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await get_active_channel_by_identifier(identifier, channel_type)

@pytest.mark.asyncio
async def test_get_chat_history_success():
    bot_id = "test_bot_id"
    skip = 0
    limit = 1000

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

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.MagicMock()
    mock_execute_result.__iter__.return_value = iter([iter([mock_session_object]), iter([mock_user_object])])
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        
        result = await get_chat_history(bot_id, skip, limit)

        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2 

        assert result[0] == [mock_session_object]
        assert result[1] == [mock_user_object]

        mock_session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_chat_history_failure():

    bot_id = "test_bot_id"
    skip = 0
    limit = 1000
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', side_effect=Exception("Database error")):
        with pytest.raises(Exception):
            await get_chat_history(bot_id, skip, limit)