import os
from pathlib import Path
import shutil
from unittest.mock import MagicMock, patch, AsyncMock
import pytest
from lib.data_models import BotConfig, Flow, Bot, FlowIntent, BotIntent

mock_extension = MagicMock()


@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
@patch("src.handlers.bot_install.create_bot", return_value=AsyncMock())
@patch("src.handlers.bot_install.install_bot", return_value=AsyncMock())
async def test_handle_bot_install_with_valid_bot_config(
    mock_install_bot, mock_create_bot
):
    flow_input = Flow(
        source="api",
        intent=FlowIntent.BOT,
        bot_config=BotConfig(
            bot_id="test_bot_id",
            intent=BotIntent.INSTALL,
            bot=Bot(
                name="test_bot_name",
                fsm_code="test_bot_fsm_code",
                requirements_txt="test_bot_requirements_txt",
                index_urls=["test_index_urls"],
                required_credentials=["API_KEY"],
                version="0.0.1",
            ),
        ),
    )

    from src.handlers.flow_input import handle_flow_input

    await handle_flow_input(flow_input)

    mock_install_bot.assert_awaited_once_with(
        bot_id="test_bot_id",
        bot_fsm_code="test_bot_fsm_code",
        bot_requirements_txt="test_bot_requirements_txt",
        index_urls=["test_index_urls"],
    )
    mock_create_bot.assert_awaited_once_with(
        bot_id="test_bot_id",
        name="test_bot_name",
        code="test_bot_fsm_code",
        requirements="test_bot_requirements_txt",
        index_urls=["test_index_urls"],
        required_credentials=["API_KEY"],
        version="0.0.1",
    )


@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
@patch("src.handlers.bot_install.delete_bot", return_value=AsyncMock())
async def test_handle_bot_delete(mock_delete_bot):
    flow_input = Flow(
        source="some_invalid_source",
        intent=FlowIntent.BOT,
        bot_config=BotConfig(
            bot_id="test_bot_id",
            intent=BotIntent.DELETE,
        ),
    )
    from src.handlers.flow_input import handle_flow_input

    await handle_flow_input(flow_input)

    mock_delete_bot.assert_awaited_once_with("test_bot_id")

@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_bot_install_with_bot_config_missing_bot():

    mock_flow_input = MagicMock(spec = Flow)

    mock_flow_input.intent = FlowIntent.BOT
    mock_flow_input.bot_config = MagicMock(spec = BotConfig)
    mock_flow_input.bot_config.intent = BotIntent.INSTALL
    mock_flow_input.bot_config.bot = None

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Bot config missing bot")

@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_bot_with_invalid_bot_config_intent():

    mock_flow_input = MagicMock(spec = Flow)

    mock_flow_input.intent = FlowIntent.BOT
    mock_flow_input.bot_config = MagicMock(spec = BotConfig)
    mock_flow_input.bot_config.intent = "invalid_bot_config_intent"

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Invalid intent in bot config")

@pytest.mark.asyncio
async def test_install_bot():

    bot_id = "test_bot_id"
    bot_fsm_code = "test_bot_fsm_code"
    bot_requirements_txt = "test_requirements"
    index_urls = {"index_url_1":"test_url_1","index_url_2":"test_url_2"}

    mock_install_command = MagicMock(spec=list)
    mock_install_command.extend.return_value = None 
    
    from src.handlers.bot_install import install_bot

    with patch.object(Path, "mkdir", return_value = AsyncMock()), \
        patch.object(shutil, "copytree", return_value = None) as mock_copytree, \
            patch.object(shutil, "copy2", return_value = None) as mock_copy2, \
                patch.object(Path, "write_text", return_value = AsyncMock()),\
                    patch('src.handlers.bot_install.subprocess.run', return_value = None) as mock_subprocess_run:
        
        result = await install_bot(bot_id, bot_fsm_code, bot_requirements_txt, index_urls)

        assert result is None
        assert mock_subprocess_run.call_count == 2
        mock_copytree.assert_not_called()
        mock_copy2.assert_called_once()

@pytest.mark.asyncio
async def test_delete_bot():

    bot_id = "test_bot_id"

    with patch.object(shutil, "rmtree", return_value = None) as mock_rmtree:
        from src.handlers.bot_install import delete_bot

        await delete_bot(bot_id)

        mock_rmtree.assert_called_once() 



@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_flow_input_when_flow_intent_is_bot_and_bot_config_not_found():

    mock_flow_input = MagicMock(spec = Flow)
    mock_flow_input.intent = FlowIntent.BOT
    mock_flow_input.bot_config = None

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Bot config not found in flow input")