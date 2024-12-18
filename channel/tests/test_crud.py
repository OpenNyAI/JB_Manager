import pytest
from unittest import mock
from lib.db_session_handler import DBSessionHandler
from lib.models import JBUser, JBChannel, JBForm
from src.crud import (
    get_channel_by_turn_id,
    get_form_parameters,
    create_message,
    get_user_by_turn_id,
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
async def test_get_channel_by_turn_id():

    turn_id = "test_turn_id"

    mock_channel = JBChannel(
        app_id="test_number",
        key="encrypted_credentials",
        type="pinnacle_whatsapp",
        url="https://api.pinnacle.com",
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_channel 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_channel_by_turn_id(turn_id)

        assert result.app_id == mock_channel.app_id
        mock_session.execute.assert_awaited_once() 

@pytest.mark.asyncio
async def test_create_message_success():
    turn_id = "test_turn_id"
    message_type = "text"
    message = {"text": "Hi"}
    is_user_sent = False

    mock_session = mock.Mock()
    mock_session.commit = mock.AsyncMock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        msg_id = await create_message(turn_id, message_type, message, is_user_sent)
        
        assert msg_id is not None

@pytest.mark.asyncio
async def test_get_user_by_turn_id():

    turn_id = "test_turn_id"

    mock_user = JBUser(
        id = turn_id,
    )
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_user 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_user_by_turn_id(turn_id)

        assert isinstance(result, JBUser) 
        assert result.id == turn_id
        mock_session.execute.assert_awaited_once()

@pytest.mark.asyncio
async def test_get_form_parameters():

    channel_id = "test_channel_id"
    form_uid = "test_form_uid"

    mock_form = JBForm(
        form_uid = form_uid,
        channel_id = channel_id,
    )

    mock_form.parameters = {"Param": "Value"}
    
    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = mock_form
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

        result = await get_form_parameters(channel_id, form_uid)
        assert result == mock_form.parameters
        mock_session.execute.assert_awaited_once()
