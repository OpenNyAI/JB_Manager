from itertools import product
from unittest.mock import MagicMock, patch, AsyncMock
import json
import pytest
from lib.models import JBBot
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
    Logger,
    FlowLogger,
)

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

flow_logger_input = Logger(
    source = "flow",
    logger_obj = FlowLogger(
        id = "1234",
        turn_id = "turn_id",
        session_id = "session_id",
        msg_id ="msg_id",
        msg_intent = "msg_intent",
        flow_intent = "flow_intent",
        sent_to_service = "sent_to_service",
        status = "status",
    )
)

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

    with patch("src.handlers.bot_input.create_flow_logger_input",return_value=flow_logger_input):
        await handle_flow_input(flow_input)

    mock_produce_message.assert_any_call(flow_output)
    mock_produce_message.assert_any_call(flow_logger_input)
    mock_update_state_and_variables.assert_called_once_with(
        "test_session_id",
        "zerotwo",
        {"state": "test_state", "variables": {"test_key": "test_value"}},
    )
