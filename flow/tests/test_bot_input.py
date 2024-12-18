from itertools import product
from unittest.mock import MagicMock, patch, AsyncMock
import json
import pytest
from datetime import datetime, timedelta
from lib.models import JBBot, JBFSMState, JBSession
from lib.data_models import (
    Flow,
    FlowIntent,
    Callback,
    CallbackType,
    UserInput,
    RAGResponse,
    Language,
    LanguageIntent,
    FSMOutput,
    FSMInput,
    FSMIntent,
    MessageType,
    Message,
    TextMessage,
    InteractiveReplyMessage,
    Option,
    FormReplyMessage,
    DialogMessage,
    Dialog,
    DialogOption,
    ButtonMessage,
    ListMessage,
    ImageMessage,
    DocumentMessage,
    FormMessage,
    Channel,
    ChannelIntent,
    RAG,
    RAGQuery,
)

mock_extension = MagicMock()

mock_bot = JBBot(
    id="test_bot_id",
    name="test_bot_name",
    status="active",
    dsl="",
    code="test_code",
    requirements="test_requirements",
    index_urls=["test_index_urls"],
    config_env={"API_SECRET": "test_api_secret"},
    required_credentials=["API_KEY", "API_SECRET"],
    credentials={
        "API_KEY": "test_api_key",
        "API_SECRET": "test_api_secret",
    },
    version="0.0.1",
)


flow_inputs = {
    "language": Flow(
        source="language",
        intent=FlowIntent.USER_INPUT,
        user_input=UserInput(
            turn_id="test_turn_id",
            message=Message(
                message_type=MessageType.TEXT,
                text=TextMessage(body="test_body_text"),
            ),
        ),
    ),
    "api": Flow(
        source="api",
        intent=FlowIntent.CALLBACK,
        callback=Callback(
            turn_id="test_turn_id",
            callback_type=CallbackType.EXTERNAL,
            external='{"test_plugin_key": "test_plugin_value"}',
        ),
    ),
    "retriever": Flow(
        source="api",
        intent=FlowIntent.CALLBACK,
        callback=Callback(
            turn_id="test_turn_id",
            callback_type=CallbackType.RAG,
            rag_response=[
                RAGResponse(chunk="test_chunk_text_1"),
                RAGResponse(chunk="test_chunk_text_2"),
            ],
        ),
    ),
    "channel_interactive": Flow(
        source="channel",
        intent=FlowIntent.USER_INPUT,
        user_input=UserInput(
            turn_id="test_turn_id",
            message=Message(
                message_type=MessageType.INTERACTIVE_REPLY,
                interactive_reply=InteractiveReplyMessage(
                    options=[
                        Option(
                            option_id="test_option_id_1",
                            option_text="test_option_text_1",
                        ),
                        Option(
                            option_id="test_option_id_2",
                            option_text="test_option_text_2",
                        ),
                    ]
                ),
            ),
        ),
    ),
    "channel_form": Flow(
        source="channel",
        intent=FlowIntent.USER_INPUT,
        user_input=UserInput(
            turn_id="test_turn_id",
            message=Message(
                message_type=MessageType.FORM_REPLY,
                form_reply=FormReplyMessage(
                    form_data={"test_form_key": "test_form_value"}
                ),
            ),
        ),
    ),
    "channel_conversation_reset": Flow(
        source="channel",
        intent=FlowIntent.DIALOG,
        dialog=Dialog(
            turn_id="test_turn_id",
            message=Message(
                message_type=MessageType.DIALOG,
                dialog=DialogMessage(
                    dialog_id=DialogOption.CONVERSATION_RESET,
                ),
            ),
        ),
    ),
    "channel_language_selected": Flow(
        source="channel",
        intent=FlowIntent.DIALOG,
        dialog=Dialog(
            turn_id="test_turn_id",
            message=Message(
                message_type=MessageType.DIALOG,
                dialog=DialogMessage(
                    dialog_id=DialogOption.LANGUAGE_SELECTED,
                    dialog_input="test_language",
                ),
            ),
        ),
    ),
}

fsm_and_assertions = {
    "out_text": (
        FSMOutput(
            intent=FSMIntent.SEND_MESSAGE,
            message=Message(
                message_type=MessageType.TEXT,
                text=TextMessage(body="test_text"),
            ),
        ),
        Language(
            source="flow",
            turn_id="test_turn_id",
            intent=LanguageIntent.LANGUAGE_OUT,
            message=Message(
                message_type=MessageType.TEXT,
                text=TextMessage(body="test_text"),
            ),
        ),
    ),
    "out_button": (
        FSMOutput(
            intent=FSMIntent.SEND_MESSAGE,
            message=Message(
                message_type=MessageType.BUTTON,
                button=ButtonMessage(
                    body="test_text",
                    header="test_header",
                    footer="test_footer",
                    options=[
                        Option(option_id="test_id_1", option_text="test_title_1"),
                        Option(option_id="test_id_2", option_text="test_title_2"),
                    ],
                ),
            ),
        ),
        Language(
            source="flow",
            turn_id="test_turn_id",
            intent=LanguageIntent.LANGUAGE_OUT,
            message=Message(
                message_type=MessageType.BUTTON,
                button=ButtonMessage(
                    body="test_text",
                    header="test_header",
                    footer="test_footer",
                    options=[
                        Option(option_id="test_id_1", option_text="test_title_1"),
                        Option(option_id="test_id_2", option_text="test_title_2"),
                    ],
                ),
            ),
        ),
    ),
    "out_list": (
        FSMOutput(
            intent=FSMIntent.SEND_MESSAGE,
            message=Message(
                message_type=MessageType.OPTION_LIST,
                option_list=ListMessage(
                    body="test_text",
                    header="test_header",
                    footer="test_footer",
                    options=[
                        Option(option_id="test_id_1", option_text="test_title_1"),
                        Option(option_id="test_id_2", option_text="test_title_2"),
                    ],
                    button_text="test_button_text",
                    list_title="test_list_title",
                ),
            ),
        ),
        Language(
            source="flow",
            turn_id="test_turn_id",
            intent=LanguageIntent.LANGUAGE_OUT,
            message=Message(
                message_type=MessageType.OPTION_LIST,
                option_list=ListMessage(
                    body="test_text",
                    header="test_header",
                    footer="test_footer",
                    options=[
                        Option(option_id="test_id_1", option_text="test_title_1"),
                        Option(option_id="test_id_2", option_text="test_title_2"),
                    ],
                    button_text="test_button_text",
                    list_title="test_list_title",
                ),
            ),
        ),
    ),
    "out_image": (
        FSMOutput(
            intent=FSMIntent.SEND_MESSAGE,
            message=Message(
                message_type=MessageType.IMAGE,
                image=ImageMessage(
                    url="test_media_url",
                    caption="test_text",
                ),
            ),
        ),
        Language(
            source="flow",
            turn_id="test_turn_id",
            intent=LanguageIntent.LANGUAGE_OUT,
            message=Message(
                message_type=MessageType.IMAGE,
                image=ImageMessage(
                    url="test_media_url",
                    caption="test_text",
                ),
            ),
        ),
    ),
    "out_document": (
        FSMOutput(
            intent=FSMIntent.SEND_MESSAGE,
            message=Message(
                message_type=MessageType.DOCUMENT,
                document=DocumentMessage(
                    url="test_media_url",
                    caption="test_text",
                    name="test_name",
                ),
            ),
        ),
        Language(
            source="flow",
            turn_id="test_turn_id",
            intent=LanguageIntent.LANGUAGE_OUT,
            message=Message(
                message_type=MessageType.DOCUMENT,
                document=DocumentMessage(
                    url="test_media_url",
                    caption="test_text",
                    name="test_name",
                ),
            ),
        ),
    ),
    "out_form": (
        FSMOutput(
            intent=FSMIntent.SEND_MESSAGE,
            message=Message(
                message_type=MessageType.FORM,
                form=FormMessage(
                    header="test_header",
                    footer="test_footer",
                    body="test_text",
                    form_id="test_form_id",
                ),
            ),
        ),
        Channel(
            source="flow",
            intent=ChannelIntent.CHANNEL_OUT,
            turn_id="test_turn_id",
            bot_output=Message(
                message_type=MessageType.FORM,
                form=FormMessage(
                    header="test_header",
                    footer="test_footer",
                    body="test_text",
                    form_id="test_form_id",
                ),
            ),
        ),
    ),
    "conversation_reset": (
        FSMOutput(
            intent=FSMIntent.CONVERSATION_RESET,
        ),
        Flow(
            source="flow",
            intent=FlowIntent.DIALOG,
            dialog=Dialog(
                turn_id="test_turn_id",
                message=Message(
                    message_type=MessageType.DIALOG,
                    dialog=DialogMessage(
                        dialog_id=DialogOption.CONVERSATION_RESET,
                    ),
                ),
            ),
        ),
    ),
    "select_language": (
        FSMOutput(
            intent=FSMIntent.LANGUAGE_CHANGE,
        ),
        Channel(
            source="flow",
            intent=ChannelIntent.CHANNEL_OUT,
            turn_id="test_turn_id",
            bot_output=Message(
                message_type=MessageType.DIALOG,
                dialog=DialogMessage(
                    dialog_id=DialogOption.LANGUAGE_CHANGE,
                ),
            ),
        ),
    ),
    "rag": (
        FSMOutput(
            intent=FSMIntent.RAG_CALL,
            rag_query=RAGQuery(
                type="default",
                collection_name="test_collection",
                query="test_query",
                top_chunk_k_value=5,
                do_hybrid_search=False,
            ),
        ),
        RAG(
            source="flow",
            type="default",
            turn_id="test_turn_id",
            collection_name="test_collection",
            query="test_query",
            top_chunk_k_value=5,
            do_hybrid_search=False
        ),
    ),
}

test_cases = {
    f"{flow_input.source}_{name}_{input_name}": (flow_input, fsm_output, flow_output)
    for (input_name, flow_input), (name, (fsm_output, flow_output)) in product(
        flow_inputs.items(), fsm_and_assertions.items()
    )
}


mock_produce_message = MagicMock()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "flow_input, mock_fsm_output, flow_output",
    list(test_cases.values()),
    ids=list(test_cases.keys()),
)
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
@patch("src.handlers.bot_input.get_state_by_session_id", return_value=AsyncMock())
@patch("src.handlers.bot_input.update_state_and_variables", return_value=AsyncMock())
@patch("src.handlers.bot_input.get_bot_by_session_id", return_value=mock_bot)
@patch("src.handlers.bot_input.subprocess.run", return_value=MagicMock())
@patch("src.handlers.bot_input.update_user_language", return_value=AsyncMock())
@patch("src.handlers.bot_input.manage_session", return_value=AsyncMock())
@patch("src.handlers.bot_input.create_message", return_value=AsyncMock())
async def test_handle_flow_input(
    mock_create_message,
    mock_manage_session,
    mock_update_user_language,
    mock_subprocess_run,
    mock_get_bot_by_session_id,
    mock_update_state_and_variables,
    mock_get_state_by_session_id,
    flow_input,
    mock_fsm_output,
    flow_output,
):
    mock_produce_message.reset_mock()

    mock_manage_session.return_value = MagicMock(id="test_session_id")

    mock_state = MagicMock(variables={"test_key": "test_value"})
    mock_get_state_by_session_id.return_value = mock_state
    mock_subprocess_run.return_value = MagicMock(
        stdout=f'{json.dumps({"fsm_output": json.loads(mock_fsm_output.model_dump_json())})}\n{json.dumps({"new_state": {"state": "test_state", "variables": {"test_key": "test_value"}}})}',
        stderr=None,
    )

    from src.handlers.flow_input import handle_flow_input

    await handle_flow_input(flow_input)

    mock_produce_message.assert_called_once_with(flow_output)
    mock_update_state_and_variables.assert_called_once_with(
        "test_session_id",
        "zerotwo",
        {"state": "test_state", "variables": {"test_key": "test_value"}},
    )

@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_flow_input_when_flow_intent_is_dialog_and_dialog_not_found():

    mock_flow_input = MagicMock(spec = Flow)
    mock_flow_input.intent = FlowIntent.DIALOG
    mock_flow_input.dialog = None

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Dialog not found in flow input")

@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_flow_input_when_flow_intent_is_callback_and_callback_not_found():

    mock_flow_input = MagicMock(spec = Flow)
    mock_flow_input.intent = FlowIntent.CALLBACK
    mock_flow_input.callback = None

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Callback not found in flow input")

@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_flow_input_when_flow_intent_is_user_input_and_user_input_not_found():

    mock_flow_input = MagicMock(spec = Flow)
    mock_flow_input.intent = FlowIntent.USER_INPUT
    mock_flow_input.user_input = None

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("User input not found in flow input")

@pytest.mark.asyncio
@patch.dict("sys.modules", {"src.extensions": mock_extension})
async def test_handle_flow_input_for_invalid_flow_intent():

    mock_flow_input = MagicMock(spec = Flow)
    mock_flow_input.intent = "test_invalid_flow_intent"

    from src.handlers.flow_input import handle_flow_input

    with patch("src.handlers.flow_input.logger") as mock_logger:
        result = await handle_flow_input(mock_flow_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Invalid flow intent: test_invalid_flow_intent")

@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
def test_handle_bot_output_when_message_not_found_in_fsm_output_for_send_message_fsm_intent():

    mock_produce_message.reset_mock()

    turn_id = "test_turn_id"
    mock_fsm_output = MagicMock(spec = FSMOutput)
    mock_fsm_output.intent = FSMIntent.SEND_MESSAGE
    mock_fsm_output.message = None
    
    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_bot_output

        result = handle_bot_output(mock_fsm_output, turn_id)

        assert result is None

        mock_logger.error.asset_called_once_with("Message not found in fsm output")

@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
def test_handle_bot_output_when_rag_query_not_found_in_fsm_output_for_fsm_intent_rag_call():

    mock_produce_message.reset_mock()

    turn_id = "test_turn_id"
    mock_fsm_output = MagicMock(spec = FSMOutput)
    mock_fsm_output.intent = FSMIntent.RAG_CALL
    mock_fsm_output.rag_query = None
    
    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_bot_output

        result = handle_bot_output(mock_fsm_output, turn_id)

        assert result is None

        mock_logger.error.asset_called_once_with("RAG query not found in fsm output")

@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
def test_handle_bot_output_for_invalid_intent_in_fsm_output():

    mock_produce_message.reset_mock()

    turn_id = "test_turn_id"
    mock_fsm_output = MagicMock(spec = FSMOutput)
    mock_fsm_output.intent = "test_invalid_intent"
    
    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_bot_output

        result = handle_bot_output(mock_fsm_output, turn_id)

        assert result is NotImplemented

        mock_logger.error.asset_called_once_with("Invalid intent in fsm output")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_manage_session_for_new_session():

    mock_produce_message.reset_mock()

    turn_id = "test_turn_id"
    new_session = True

    mock_session = JBSession(id="test_session_id", user_id="test_user_id1", channel_id="test_channel_id1")
    
    with patch("src.handlers.bot_input.create_session", return_value = mock_session) as mock_create_session:
        from src.handlers.bot_input import manage_session

        result_session = await manage_session(turn_id, new_session)

        assert result_session is not None
        assert isinstance(result_session, JBSession)
        assert result_session.id == mock_session.id
        assert result_session.user_id == mock_session.user_id
        assert result_session.channel_id == mock_session.channel_id

        mock_create_session.assert_awaited_once_with(turn_id)
        
@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_manage_session_when_session_not_found():

    mock_produce_message.reset_mock()

    turn_id = "test_turn_id"
    new_session = False

    mock_session = JBSession(id="test_session_id", 
                             user_id="test_user_id1", 
                             channel_id="test_channel_id1")
    
    with patch("src.handlers.bot_input.get_session_by_turn_id", return_value = None) as mock_get_session_by_turn_id, \
        patch("src.handlers.bot_input.create_session", return_value = mock_session) as mock_create_session:
        from src.handlers.bot_input import manage_session

        result_session = await manage_session(turn_id, new_session)

        assert result_session is not None
        assert isinstance(result_session, JBSession)
        assert result_session.id == mock_session.id
        assert result_session.user_id == mock_session.user_id
        assert result_session.channel_id == mock_session.channel_id

        mock_get_session_by_turn_id.assert_awaited_once_with(turn_id)
        mock_create_session.assert_awaited_once_with(turn_id)

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_manage_session_when_session_updating():

    mock_produce_message.reset_mock()

    turn_id = "test_turn_id"
    new_session = False

    mock_session = JBSession(id="test_session_id", 
                             user_id="test_user_id", 
                             channel_id="test_channel_id",
                             updated_at = datetime.now() - timedelta(hours=1))
    
    with patch("src.handlers.bot_input.get_session_by_turn_id", return_value = mock_session) as mock_get_session_by_turn_id, \
        patch("src.handlers.bot_input.update_session", return_value = None) as mock_update_session, \
            patch("src.handlers.bot_input.update_turn", return_value = None) as mock_update_turn:
        
        from src.handlers.bot_input import manage_session

        result_session = await manage_session(turn_id, new_session)

        assert result_session is not None
        assert isinstance(result_session, JBSession)
        assert result_session.id == mock_session.id
        assert result_session.user_id == mock_session.user_id
        assert result_session.channel_id == mock_session.channel_id

        mock_get_session_by_turn_id.assert_awaited_once_with(turn_id)
        mock_update_session.assert_awaited_once_with(mock_session.id)
        mock_update_turn.assert_awaited_once_with(session_id=mock_session.id, turn_id=turn_id)

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_bot_input_when_bot_not_found_for_given_session_id():

    mock_produce_message.reset_mock()

    mock_state = MagicMock()
    
    mock_fsm_input = MagicMock(spec= FSMInput)
    mock_session_id = "test_session_id"

    with patch("src.handlers.bot_input.get_state_by_session_id", return_value = mock_state) as mock_get_state_by_session_id, \
        patch("src.handlers.bot_input.get_bot_by_session_id", return_value = None) as mock_get_bot_by_session_id, \
            patch("src.handlers.bot_input.logger") as mock_logger:
        
        from src.handlers.bot_input import handle_bot_input

        result = [item async for item in handle_bot_input(mock_fsm_input, mock_session_id)]  

        assert result==[]

        mock_get_state_by_session_id.assert_awaited_once_with(mock_session_id)
        mock_get_bot_by_session_id.assert_awaited_once_with(mock_session_id)
        mock_logger.error.asset_called_once_with("Bot not found for session_id: test_session_id")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_bot_input_when_error_in_running_fsm():

    mock_produce_message.reset_mock()

    mock_fsm_input = MagicMock(spec= FSMInput)
    mock_fsm_input.model_dump.return_value = mock_fsm_input

    mock_session_id = "test_session_id"

    mock_state = MagicMock(spec= JBFSMState)
    mock_state.variables={"test_key": "test_value"}

    mock_completed_process = MagicMock()
    mock_completed_process.stderr = "test_error_message"

    with patch("src.handlers.bot_input.get_state_by_session_id", return_value = mock_state) as mock_get_state_by_session_id, \
        patch("src.handlers.bot_input.get_bot_by_session_id", return_value = mock_bot) as mock_get_bot_by_session_id, \
            patch("subprocess.run", return_value = mock_completed_process), \
                patch("json.dumps", return_value = MagicMock()), \
                    patch("src.handlers.bot_input.logger") as mock_logger:
        
        from src.handlers.bot_input import handle_bot_input

        result = [item async for item in handle_bot_input(mock_fsm_input, mock_session_id)]  

        assert result==[]

        mock_get_state_by_session_id.assert_awaited_once_with(mock_session_id)
        mock_get_bot_by_session_id.assert_awaited_once_with(mock_session_id)
        mock_logger.error.asset_called_once_with("Error while running fsm: test_error_message")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_user_input_when_text_not_found():

    mock_produce_message.reset_mock()

    mock_user_input = MagicMock(spec = UserInput)
    mock_user_input.turn_id = "test_turn_id"

    mock_user_input.message = MagicMock(spec = Message)
    mock_user_input.message.message_type = MessageType.TEXT
    mock_user_input.message.text = None

    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_user_input

        result = await handle_user_input(mock_user_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Text not found in user input")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_user_input_when_interactive_reply_not_found():

    mock_produce_message.reset_mock()

    mock_user_input = MagicMock(spec = UserInput)
    mock_user_input.turn_id = "test_turn_id"
    
    mock_user_input.message = MagicMock(spec = Message)
    mock_user_input.message.message_type = MessageType.INTERACTIVE_REPLY
    mock_user_input.message.interactive_reply = None

    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_user_input

        result = await handle_user_input(mock_user_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Interactive reply not found in user input")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_user_input_when_form_reply_not_found():

    mock_produce_message.reset_mock()

    mock_user_input = MagicMock(spec = UserInput)
    mock_user_input.turn_id = "test_turn_id"
    
    mock_user_input.message = MagicMock(spec = Message)
    mock_user_input.message.message_type = MessageType.FORM_REPLY
    mock_user_input.message.form_reply = None

    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_user_input

        result = await handle_user_input(mock_user_input)

        assert result is None

        mock_logger.error.asset_called_once_with("Form reply not found in user input")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_user_input_when_message_type_not_implemented_or_invalid():

    mock_produce_message.reset_mock()

    mock_user_input = MagicMock(spec = UserInput)
    mock_user_input.turn_id = "test_turn_id"
    
    mock_user_input.message = MagicMock(spec = Message)
    mock_user_input.message.message_type = "test_not_implemented_message_type"

    from src.handlers.bot_input import handle_user_input

    result = await handle_user_input(mock_user_input)

    assert result is NotImplemented

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_callback_input_when_rag_response_not_found():

    mock_produce_message.reset_mock()

    mock_callback = MagicMock(spec = Callback)
    mock_callback.turn_id = "test_turn_id"
    mock_callback.callback_type = CallbackType.RAG 
    mock_callback.rag_response = None

    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_callback_input

        result = await handle_callback_input(mock_callback)

        assert result is None

        mock_logger.error.asset_called_once_with("RAG response not found in callback input")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_dialog_input_when_message_not_found():

    mock_produce_message.reset_mock()

    mock_dialog = MagicMock(spec = Dialog)
    mock_dialog.turn_id = "test_turn_id"

    mock_dialog.message = MagicMock(spec = Message)
    mock_dialog.message.dialog = None 

    with patch("src.handlers.bot_input.logger") as mock_logger:
        from src.handlers.bot_input import handle_dialog_input

        result = await handle_dialog_input(mock_dialog)

        assert result is None

        mock_logger.error.asset_called_once_with("Message not found in dialog input")

@pytest.mark.asyncio
@patch.dict(
    "sys.modules", {"src.extensions": MagicMock(produce_message=mock_produce_message)}
)
async def test_handle_dialog_input_when_dialog_option_not_implemented():

    mock_produce_message.reset_mock()

    mock_dialog = MagicMock(spec = Dialog)
    mock_dialog.turn_id = "test_turn_id"
    mock_dialog.message = MagicMock(spec = Message)

    mock_dialog.message.dialog = MagicMock(spec = DialogMessage)
    mock_dialog.message.dialog.dialog_id = "test_not_implemented_dialog_option"
    
    from src.handlers.bot_input import handle_dialog_input

    result = await handle_dialog_input(mock_dialog)

    assert result is NotImplemented