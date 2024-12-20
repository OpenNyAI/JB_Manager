import logging
import uuid
import json
import subprocess
from datetime import datetime
from pathlib import Path
from lib.data_models import (
    FSMOutput,
    Language,
    LanguageIntent,
    Channel,
    ChannelIntent,
    FSMInput,
    FSMIntent,
    Message,
    MessageType,
    Flow,
    FlowIntent,
    DialogMessage,
    DialogOption,
    Dialog,
    RAG,
    UserInput,
    Callback,
    CallbackType,
    Logger,
    FlowLogger,
)
from ..crud import (
    get_bot_by_session_id,
    get_session_by_turn_id,
    get_state_by_session_id,
    insert_state,
    update_state_and_variables,
    create_message,
    create_session,
    update_session,
    update_turn,
    update_user_language,
    insert_jb_webhook_reference,
    update_api_logger,
)
from ..extensions import produce_message
from ..crud import get_msg_id_by_turn_id

logger = logging.getLogger("flow")

async def create_flow_logger_input(
        turn_id: str, 
        session_id: str, 
        msg_intent: str, 
        flow_intent: str, 
        sent_to_service: str,
        status: str):

    id = str(uuid.uuid4())
    if msg_intent == "Incoming":
        msg_id = await get_msg_id_by_turn_id(turn_id = turn_id, msg_intent = msg_intent)
        if msg_id is None :
            msg_id = ""
    else:
        msg_id = str(uuid.uuid4())
    
    flow_logger_input = Logger(
        source = "flow",
        logger_obj = FlowLogger(
            id = id,
            turn_id = turn_id,
            session_id = session_id,
            msg_id =msg_id,
            msg_intent = msg_intent,
            flow_intent = flow_intent,
            sent_to_service = sent_to_service,
            status = status,
        )
    )
    return flow_logger_input

async def handle_bot_output(fsm_output: FSMOutput, turn_id: str, session_id: str, flow_intent: str):
    flow_logger_object: Logger
    intent = fsm_output.intent
    if intent == FSMIntent.SEND_MESSAGE:
        message = fsm_output.message
        if not message:
            logger.error("Message not found in fsm output")
            return
        message_type = message.message_type
        if message_type == MessageType.FORM:
            destination = "channel"
            flow_output = Channel(
                source="flow",
                turn_id=turn_id,
                intent=ChannelIntent.CHANNEL_OUT,
                bot_output=message,
            )
        else:
            destination = "language"
            flow_output = Language(
                source="flow",
                turn_id=turn_id,
                intent=LanguageIntent.LANGUAGE_OUT,
                message=message,
            )
    elif intent == FSMIntent.CONVERSATION_RESET:
        destination = "flow"
        flow_output = Flow(
            source="flow",
            intent=FlowIntent.DIALOG,
            dialog=Dialog(
                turn_id=turn_id,
                message=Message(
                    message_type=MessageType.DIALOG,
                    dialog=DialogMessage(dialog_id=DialogOption.CONVERSATION_RESET),
                ),
            ),
        )
    elif intent == FSMIntent.LANGUAGE_CHANGE:
        destination = "channel"
        flow_output = Channel(
            source="flow",
            turn_id=turn_id,
            intent=ChannelIntent.CHANNEL_OUT,
            bot_output=Message(
                message_type=MessageType.DIALOG,
                dialog=DialogMessage(dialog_id=DialogOption.LANGUAGE_CHANGE),
            ),
        )
    elif intent == FSMIntent.RAG_CALL:
        destination = "rag"
        rag_query = fsm_output.rag_query
        if not rag_query:
            logger.error("RAG query not found in fsm output")
            return
        flow_output = RAG(
            type=rag_query.type,
            source="flow",
            turn_id=turn_id,
            collection_name=rag_query.collection_name,
            query=rag_query.query,
            top_chunk_k_value=rag_query.top_chunk_k_value,
            do_hybrid_search=rag_query.do_hybrid_search
        )
    else:
        logger.error("Invalid intent in fsm output")
        flow_logger_object = await create_flow_logger_input(
            turn_id=turn_id, 
            session_id=session_id, 
            msg_intent = "Not Implemented", 
            flow_intent = "Not Implemented", 
            sent_to_service="",
            status="Invalid intent in fsm output"
        )
        return NotImplemented, flow_logger_object
    
    logger.info("Output to %s: %s", destination, flow_output)
    if isinstance(flow_output, Flow) or isinstance(flow_output, RAG):
        msg_intent = "Incoming"
        sent_to_service = "Flow" if isinstance(flow_output, Flow) else "Retriever"
    elif isinstance(flow_output, Channel) or isinstance(flow_output, Language):
        msg_intent = "Outgoing"
        sent_to_service = "Channel" if isinstance(flow_output, Channel) else "Language"

    flow_logger_object = await create_flow_logger_input(
            turn_id=turn_id, 
            session_id=session_id, 
            msg_intent = msg_intent, 
            flow_intent = flow_intent, 
            sent_to_service=sent_to_service,
            status="Success"
        )
    return flow_output, flow_logger_object


async def manage_session(turn_id: str, new_session: bool = False):
    if new_session:
        logger.info("Creating new session for turn_id: %s", turn_id)
        session = await create_session(turn_id)
    else:
        logger.info("Managing session for turn_id: %s", turn_id)
        session = await get_session_by_turn_id(turn_id)
        timeout = 60 * 60 * 24 * 1000  # 24 hours
        if not session:
            logger.info("Session not found for turn_id: %s", turn_id)
            session = await create_session(turn_id)
        elif session.updated_at.timestamp() + timeout < datetime.now().timestamp():
            logger.info("Session expired for turn_id: %s", turn_id)
            session = await create_session(turn_id)
        else:
            logger.info("Updating session for turn_id: %s", turn_id)
            await update_session(session.id)
            await update_turn(session_id=session.id, turn_id=turn_id)
    await update_api_logger(turn_id=turn_id, session_id= session.id)
    return session


async def handle_bot_input(fsm_input: FSMInput, session_id: str):
    state = await get_state_by_session_id(session_id)
    if state is None:
        state = await insert_state(session_id, "zero")
    logger.info("State: %s", state)

    # get name from bot id
    bot_details = await get_bot_by_session_id(session_id)
    if not bot_details:
        logger.error("Bot not found for session_id: %s", session_id)
        return
    bot_id: str = bot_details.id
    bot_name: str = bot_details.name
    config_env = bot_details.config_env
    config_env = {} if config_env is None else config_env
    credentials = bot_details.credentials
    credentials = {} if credentials is None else credentials

    path = Path(__file__).parent.parent.parent / "bots" / bot_id

    ## need to pass state json and msg_text to the bot
    fsm_runner_input = {
        "fsm_input": fsm_input.model_dump(exclude_none=True),
        "state": state.variables,
        "bot_name": bot_name,
        "credentials": credentials,
        "config_env": config_env,
    }
    completed_process = subprocess.run(
        [
            str(path / ".venv" / "bin" / "python"),
            str(path / "fsm_wrapper.py"),
            json.dumps(fsm_runner_input),
        ],
        capture_output=True,
        text=True,
    )

    if completed_process.stderr:
        logger.error("Error while running fsm: %s", completed_process.stderr)
        return

    # logger.error("Output from fsm: %s", completed_process.stdout)
    for line in completed_process.stdout.split("\n"):
        if not line:
            continue
        logger.error("Output from fsm: %s", line)
        fsm_runner_output = json.loads(line)
        if "fsm_output" in fsm_runner_output:
            fsm_output = fsm_runner_output["fsm_output"]
            logger.info("Callback message: %s", fsm_output)
            fsm_output = FSMOutput.model_validate(fsm_output)
            # execute callback
            yield fsm_output
        else:
            # save new state to db
            new_state_variables = fsm_runner_output["new_state"]
            logger.info("FSM Runner message: %s", fsm_runner_output)
            await update_state_and_variables(session_id, "zerotwo", new_state_variables)


async def handle_user_input(user_input: UserInput):
    message = user_input.message
    message_type = message.message_type
    if message_type == MessageType.TEXT:
        if not message.text:
            logger.error("Text not found in user input")
            return
        # TODO: content filter
        fsm_input = FSMInput(user_input=message.text.body)
    elif message_type == MessageType.INTERACTIVE_REPLY:
        if not message.interactive_reply:
            logger.error("Interactive reply not found in user input")
            return
        selected_options = json.dumps(
            [
                option.model_dump(exclude_none=True)
                for option in message.interactive_reply.options
            ]
        )
        fsm_input = FSMInput(user_input=selected_options)
    elif message_type == MessageType.FORM_REPLY:
        if not message.form_reply:
            logger.error("Form reply not found in user input")
            return
        form_response = json.dumps(message.form_reply.form_data)
        fsm_input = FSMInput(user_input=form_response)
    elif message_type == MessageType.DOCUMENT:
        if not message.document:
            logger.error("Document not found in user input")
            return
        document_url = message.document.url
        fsm_input = FSMInput(user_input=document_url)
    elif message_type == MessageType.IMAGE:
        if not message.image:
            logger.error("Image not found in user input")
            return
        image_url = message.image.url
        logger.info(f"IMAGE URL: {image_url}, {type(image_url)}")
        fsm_input = FSMInput(user_input=image_url)
    else:
        return NotImplemented

    turn_id = user_input.turn_id
    await create_message(
        turn_id=turn_id,
        message_type=message_type.value,
        is_user_sent=True,
        message=getattr(message, message.message_type.value).model_dump_json(
            exclude_none=True
        ),
    )
    session = await manage_session(turn_id=turn_id)
    session_id: str = session.id
    async for fsm_output in handle_bot_input(fsm_input, session_id=session_id):
        # if fsm_output.intent == FSMIntent.WEBHOOK:
        #     reference_id = fsm_output.webhook.reference_id
        #     insert_jb_webhook_reference(reference_id=reference_id, turn_id=turn_id)
        # else:
        flow_output, flow_logger_object = await handle_bot_output(fsm_output, turn_id=turn_id, session_id=session_id, flow_intent = "User_input")
        produce_message(flow_output)
        produce_message(flow_logger_object)


async def handle_callback_input(callback: Callback):
    callback_type = callback.callback_type
    if callback_type == CallbackType.EXTERNAL:
        callback_input = callback.external
        fsm_input = FSMInput(callback_input=callback_input)
    elif callback_type == CallbackType.RAG:
        if not callback.rag_response:
            logger.error("RAG response not found in callback input")
            return
        callback_input = [
            resp.model_dump_json(exclude_none=True) for resp in callback.rag_response
        ]
        callback_input = json.dumps(callback_input)
        fsm_input = FSMInput(callback_input=callback_input)

    turn_id = callback.turn_id
    session = await manage_session(turn_id=turn_id)
    session_id: str = session.id
    async for fsm_output in handle_bot_input(fsm_input, session_id=session_id):
        # if fsm_output.intent == FSMIntent.WEBHOOK:
        #     reference_id = fsm_output.webhook.reference_id
        #     insert_jb_webhook_reference(reference_id=reference_id, turn_id=turn_id)
        # else:
        flow_output, flow_logger_object = await handle_bot_output(fsm_output, turn_id=turn_id, session_id=session_id, flow_intent = "Callback")
        produce_message(flow_output)
        produce_message(flow_logger_object)


async def handle_dialog_input(dialog: Dialog):
    turn_id = dialog.turn_id
    if not dialog.message.dialog:
        logger.error("Message not found in dialog input")
        return
    dialog_id = dialog.message.dialog.dialog_id
    if dialog_id == DialogOption.CONVERSATION_RESET:
        fsm_input = FSMInput(user_input="reset")
        new_session = True
    elif dialog_id == DialogOption.LANGUAGE_SELECTED:
        selected_language: str = dialog.message.dialog.dialog_input
        await update_user_language(turn_id=turn_id, selected_language=selected_language)
        fsm_input = FSMInput(user_input="language_selected")
        new_session = False
    else:
        return NotImplemented

    session = await manage_session(turn_id=turn_id, new_session=new_session)
    session_id: str = session.id
    async for fsm_output in handle_bot_input(fsm_input, session_id=session_id):
        # if fsm_output.intent == FSMIntent.WEBHOOK:
        #     reference_id = fsm_output.webhook.reference_id
        #     insert_jb_webhook_reference(reference_id=reference_id, turn_id=turn_id)
        # else:
        flow_output, flow_logger_object = await handle_bot_output(fsm_output, turn_id=turn_id, session_id=session_id, flow_intent = "Dialog")
        produce_message(flow_output)
        produce_message(flow_logger_object)
