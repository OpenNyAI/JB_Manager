import json
import pytest
from unittest import mock
from lib.db_session_handler import DBSessionHandler
from lib.models import JBBot, JBFSMState, JBSession, JBTurn
from lib.data_models import (
    MessageType,
    Message,
    TextMessage,
)

from src.crud import (
    create_bot,
    create_message,
    create_session,
    get_all_bots,
    get_bot_by_session_id,
    get_session_by_turn_id,
    get_state_by_session_id,
    insert_jb_webhook_reference, 
    insert_state, 
    update_session, 
    update_state_and_variables, 
    update_turn,
    update_user_language
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
async def test_get_state_by_session_id():

    session_id = "test_session_id"

    mock_state = JBFSMState(
        id = "test_id",
        session_id = "test_session_id",
        state = "test_state",
        variables = {"var1":"test_variable_1","var2":"test_variable_2"},
        message = "test_message",
    )

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_state 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_state_by_session_id(session_id)

        assert isinstance(result,JBFSMState)
        assert result.id == mock_state.id
        assert result.session_id == mock_state.session_id
        assert result.state == mock_state.state
        assert result.variables == mock_state.variables
        assert result.message == mock_state.message

@pytest.mark.asyncio
async def test_create_session():
    
    turn_id = "test_turn_id"
    session_id = "test_session_id"

    mock_jb_turn = JBTurn(
        id = "test_turn_id",
        session_id = "test_session_id",
        bot_id = "test_bot_id",
        channel_id = "test_channel_id",
        user_id = "test_user_id",
        turn_type = "test_turn_type"
    )

    mock_session_object = JBSession(
        id = "test_session_id",
        user_id = "test_user_id",
        channel_id = "test_channel_id" 
    )

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    
    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_jb_turn 

    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result) 

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with mock.patch("src.crud.uuid.uuid4", return_value = session_id):
            result = await create_session(turn_id)
            
            assert result is not None
            assert isinstance(result, JBSession)
            assert result.id == mock_session_object.id
            assert result.user_id == mock_session_object.user_id
            assert result.channel_id == mock_session_object.channel_id

            assert mock_session.commit.call_count == 2
            assert mock_session.begin.call_count == 3

@pytest.mark.asyncio
async def test_update_session():

    session_id = "test_session_id"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await update_session(session_id)

        assert result is None

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_turn():

    session_id = "test_session_id"
    turn_id = "test_turn_id"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await update_turn(session_id, turn_id)

        assert result is None

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_insert_state():

    session_id = "test_session_id"
    state = "test_state"
    variables = {"var1":"test_variable_1","var2":"test_variable_2"}
    
    state_id = "test_state_id"
    mock_state = JBFSMState(
        id = "test_state_id",
        session_id = "test_session_id",
        state = "test_state",
        variables = {"var1":"test_variable_1","var2":"test_variable_2"}
    )

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with mock.patch("src.crud.uuid.uuid4", return_value = state_id):
            result = await insert_state(session_id, state, variables)

            assert isinstance(result,JBFSMState)
            assert result.id == mock_state.id
            assert result.session_id == mock_state.session_id
            assert result.state == mock_state.state
            assert result.variables == mock_state.variables

            mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_state_and_variables():

    session_id = "test_session_id"
    state = "test_state"
    variables = {"var1":"test_variable_1","var2":"test_variable_2"}

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await update_state_and_variables(session_id, state, variables)

        assert result is not None
        assert result == state

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_bot_by_session_id():

    session_id = "test_session_id"

    mock_bot = JBBot( 
        id = "test_bot_id",
        name = "Bot",
        status = "active",
        dsl = "test_dsl",
        code = "test_code",
        requirements = "test_requirements",
        index_urls = {"index_url1":"test_url_1","index_url2":"test_url_2"},
        config_env = {},
        required_credentials = {"API_KEY":"test_api_key"},
        credentials = {},
        version = "0.0.1"
    )

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_bot 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_bot_by_session_id(session_id)

        assert isinstance(result,JBBot)
        assert result.id == mock_bot.id
        assert result.name == mock_bot.name
        assert result.status == mock_bot.status
        assert result.dsl == mock_bot.dsl
        assert result.code == mock_bot.code
        assert result.requirements == mock_bot.requirements
        assert result.index_urls == mock_bot.index_urls
        assert result.config_env == mock_bot.config_env
        assert result.required_credentials == mock_bot.required_credentials
        assert result.credentials == mock_bot.credentials
        assert result.version == mock_bot.version

        mock_session.execute.assert_awaited_once()  

@pytest.mark.asyncio
async def test_get_session_by_turn_id():

    turn_id = "test_turn_id"

    mock_session_object = JBSession(
        id = "test_session_id",
        user_id = "test_user_id",
        channel_id = "test_channel_id" 
    )

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_session_object 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_session_by_turn_id(turn_id)

        assert isinstance(result,JBSession)
        assert result.id == mock_session_object.id
        assert result.user_id == mock_session_object.user_id
        assert result.channel_id == mock_session_object.channel_id

        mock_session.execute.assert_awaited_once()  

@pytest.mark.asyncio
async def test_get_all_bots():

    mock_bot1 = JBBot(id="test_bot_1", name="Bot1", status="active")
    mock_bot2 = JBBot(id="test_bot_2", name="Bot2", status="inactive")

    bot_list = [mock_bot1,mock_bot2]

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.all.return_value = bot_list 

    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  
    
    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await get_all_bots()

        assert isinstance(result,list)
        assert len(result) == len(bot_list)
        for item in result:
            assert isinstance(item, JBBot)
            assert item in bot_list
        mock_session.execute.assert_awaited_once()  

def test_insert_jb_webhook_reference():

    reference_id = "test_reference_id"
    turn_id = "test_turn_id"

    with mock.patch.object(DBSessionHandler, 'get_sync_session') as mock_get_session:
        
        mock_session = mock.MagicMock()
        mock_get_session.return_value = mock_session

        mock_session.begin.return_value = mock.MagicMock()
        mock_session.commit.return_value = None 

        result = insert_jb_webhook_reference(reference_id, turn_id)

        assert result is not None 
        assert result == reference_id

@pytest.mark.asyncio
async def test_create_bot():
    
    bot_id = "test_bot_id"
    name = "test_bot"
    code = "test_code"
    requirements="test_requirements"
    index_urls = {"index_url1":"test_url_1","index_url2":"test_url_2"}
    required_credentials = {"API_KEY":"test_api_key"}
    version = "0.0.1"
    
    mock_bot = JBBot(
        id=bot_id,
        name=name,
        code=code,
        requirements=requirements,
        index_urls=index_urls,
        required_credentials=required_credentials,
        version=version,
    )

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        result = await create_bot(bot_id, name, code, requirements, index_urls, required_credentials, version)
        
        assert result is not None
        assert isinstance(result, JBBot)
        assert result.id == mock_bot.id
        assert result.name == mock_bot.name
        assert result.code == mock_bot.code
        assert result.requirements == mock_bot.requirements
        assert result.index_urls == mock_bot.index_urls
        assert result.required_credentials == mock_bot.required_credentials
        assert result.version == mock_bot.version

        mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_create_message():
    
    message_id = "test_message_id"
    message = Message(
        message_type=MessageType.TEXT,
        text=TextMessage(body="test_text_message"),
    )

    turn_id = "test_turn_id",
    message_type = "text",
    message = json.loads(getattr(message, message.message_type.value).model_dump_json(exclude_none=True))
    is_user_sent = True,

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with mock.patch("src.crud.uuid.uuid4", return_value = message_id):

            result = await create_message(turn_id, message_type, message, is_user_sent)
            
            assert result is not None
            assert result == message_id

            mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_update_user_language():

    turn_id = "test_turn_id"
    selected_language = "English"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())
    mock_session.commit = mock.AsyncMock() 
    
    mock_execute = mock.AsyncMock() 
    mock_session.execute = mock_execute

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await update_user_language(turn_id, selected_language)

        assert result is None

        mock_session.execute.assert_awaited_once() 
        mock_session.commit.assert_awaited_once()