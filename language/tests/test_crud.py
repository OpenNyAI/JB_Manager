from unittest import mock
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from src.crud import get_user_preferred_language, get_user_preferred_language_by_pid
from lib.db_session_handler import DBSessionHandler

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
async def test_get_user_preferred_language_when_pid_not_none():

    turn_id = "test_turn_id"
    pid = "test_user_id"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = pid 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with patch("src.crud.get_user_preferred_language_by_pid", return_value = "en") as mock_get_user_preferred_language_by_pid:

            result = await get_user_preferred_language(turn_id)

            assert result == "en"

            mock_get_user_preferred_language_by_pid.assert_awaited_once_with(pid)

@pytest.mark.asyncio
async def test_get_user_preferred_language_when_pid_is_none():

    turn_id = "test_turn_id"
    pid = None

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = pid 
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):
        with patch("src.crud.get_user_preferred_language_by_pid") as mock_get_user_preferred_language_by_pid:

            result = await get_user_preferred_language(turn_id)

            assert result == None
            
            mock_get_user_preferred_language_by_pid.assert_not_awaited()

@pytest.mark.asyncio
async def test_get_user_preferred_language_by_pid():

    pid = "test_user_id"
    language_preference = "en"

    mock_session = mock.Mock()
    mock_session.begin = mock.Mock(return_value=AsyncBeginMock())

    mock_execute_result = mock.Mock()
    mock_execute_result.scalars.return_value.first.return_value = language_preference
    
    mock_session.execute = mock.AsyncMock(return_value=mock_execute_result)  

    with mock.patch.object(DBSessionHandler, 'get_async_session', return_value=AsyncContextManagerMock(mock_session)):

            result = await get_user_preferred_language_by_pid(pid)

            assert result == "en"