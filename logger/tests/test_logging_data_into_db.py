from unittest.mock import patch
import pytest
from src.handlers import logging_data_into_db
from lib.data_models import (
    Logger,
    APILogger,
    ChannelLogger,
    LanguageLogger,
    FlowLogger,
    RetrieverLogger,
)

@pytest.mark.asyncio
async def test_logger_with_api_logger_object():
    api_logger_input = Logger(
        source = "api",
        logger_obj = APILogger(
            user_id = "test_user_id",
            turn_id = "test_turn_id",
            session_id = "test_session_id",
            status = "Success/Failure",
        )
    ) 

    with patch("src.handlers.create_api_logger") as mock_create_api_logger:
        await logging_data_into_db(service_name="api",input_data=api_logger_input)
        mock_create_api_logger.assert_called_once_with(user_id = api_logger_input.logger_obj.user_id, 
                                                        turn_id = api_logger_input.logger_obj.turn_id, 
                                                        session_id = api_logger_input.logger_obj.session_id, 
                                                        status = api_logger_input.logger_obj.status)

@pytest.mark.asyncio
async def test_logger_with_channel_logger_object():

    channel_logger_input = Logger(
        source = "channel",
        logger_obj = ChannelLogger(
            id = "test_id",
            turn_id="test_turn_id", 
            channel_id="test_channel_id", 
            channel_name="test_channel_name", 
            msg_intent = "Incoming/Outgoing",
            msg_type="test_msg_type", 
            sent_to_service = "Language/Flow" ,
            status = "Success"
        )
    ) 

    with patch("src.handlers.create_channel_logger") as mock_create_channel_logger:
        await logging_data_into_db(service_name="channel",input_data=channel_logger_input)
        mock_create_channel_logger.assert_called_once_with(id = channel_logger_input.logger_obj.id,
                                                           turn_id=channel_logger_input.logger_obj.turn_id, 
                                                           channel_id=channel_logger_input.logger_obj.channel_id, 
                                                           channel_name=channel_logger_input.logger_obj.channel_name, 
                                                           msg_intent = channel_logger_input.logger_obj.msg_intent,
                                                           msg_type=channel_logger_input.logger_obj.msg_type, 
                                                           sent_to_service = channel_logger_input.logger_obj.sent_to_service,
                                                           status = channel_logger_input.logger_obj.status)

@pytest.mark.asyncio
async def test_logger_with_language_logger_object():
    language_logger_input = Logger(
        source = "language",
        logger_obj = LanguageLogger(
            id = "test_id",
            turn_id = "test_turn_id",
            msg_id = "test_msg_id",
            msg_state = "Incoming/Outgoing/Intermediate",
            msg_language = "Preferred/ English",
            msg_type = "test_msg_type",
            translated_to_language = "Preferred/ English",
            translation_type = "test_translation_type",
            translation_model = "Dhruva/ Azure",
            response_time = "1.01399491",
            status = "Success"
        )
    ) 

    with patch("src.handlers.create_language_logger") as mock_create_language_logger:
        await logging_data_into_db(service_name="language",input_data=language_logger_input)
        mock_create_language_logger.assert_called_once_with(id = language_logger_input.logger_obj.id,
                                                            turn_id=language_logger_input.logger_obj.turn_id, 
                                                            msg_id=language_logger_input.logger_obj.msg_id, 
                                                            msg_state=language_logger_input.logger_obj.msg_state, 
                                                            msg_language = language_logger_input.logger_obj.msg_language,
                                                            msg_type = language_logger_input.logger_obj.msg_type,
                                                            translated_to_language = language_logger_input.logger_obj.translated_to_language,
                                                            translation_type = language_logger_input.logger_obj.translation_type,
                                                            translation_model = language_logger_input.logger_obj.translation_model,
                                                            response_time = language_logger_input.logger_obj.response_time,
                                                            status = language_logger_input.logger_obj.status)
        
@pytest.mark.asyncio
async def test_logger_with_flow_logger_object():
    flow_logger_input = Logger(
        source = "flow",
        logger_obj = FlowLogger(
            id = "test_id",
            turn_id = "test_turn_id",
            session_id = "test_session_id",
            msg_id = "test_msg_id",
            msg_intent = "Incoming/Outgoing",
            flow_intent = "Dialog/ Callback/ User input",
            sent_to_service = "Flow/RAG/Channel/Language",
            status = "Success"
        )
    ) 

    with patch("src.handlers.create_flow_logger") as mock_create_flow_logger:
        await logging_data_into_db(service_name="flow",input_data=flow_logger_input)
        mock_create_flow_logger.assert_called_once_with(id = flow_logger_input.logger_obj.id,
                                                        turn_id = flow_logger_input.logger_obj.turn_id,
                                                        session_id = flow_logger_input.logger_obj.session_id,
                                                        msg_id = flow_logger_input.logger_obj.msg_id,
                                                        msg_intent = flow_logger_input.logger_obj.msg_intent,
                                                        flow_intent = flow_logger_input.logger_obj.flow_intent,
                                                        sent_to_service = flow_logger_input.logger_obj.sent_to_service,
                                                        status = flow_logger_input.logger_obj.status)
        
@pytest.mark.asyncio
async def test_logger_with_retriever_logger_object():
    retriever_logger_input = Logger(
        source = "retriever",
        logger_obj = RetrieverLogger(
            id = "test_id",
            turn_id = "test_turn_id",
            msg_id = "test_msg_id",
            retriever_type = "r2r/ default",
            collection_name = "test_collection_name",
            top_chunk_k_value = "5",
            number_of_chunks = "400",
            chunks = ["chunk 1","chunk 2"],
            query = "test_query",
            status = "Success",
        )
    ) 

    with patch("src.handlers.create_retriever_logger") as mock_create_retriever_logger:
        await logging_data_into_db(service_name="retriever",input_data=retriever_logger_input)
        mock_create_retriever_logger.assert_called_once_with(
            id = retriever_logger_input.logger_obj.id,
            turn_id = retriever_logger_input.logger_obj.turn_id,
            msg_id = retriever_logger_input.logger_obj.msg_id,
            retriever_type = retriever_logger_input.logger_obj.retriever_type,
            collection_name = retriever_logger_input.logger_obj.collection_name,
            top_chunk_k_value = retriever_logger_input.logger_obj.top_chunk_k_value,
            number_of_chunks = retriever_logger_input.logger_obj.number_of_chunks,
            chunks = retriever_logger_input.logger_obj.chunks,
            query = retriever_logger_input.logger_obj.query,
            status = retriever_logger_input.logger_obj.status)
        
@pytest.mark.asyncio
async def test_logger_with_invalid_source():
    
    with patch("src.handlers.create_retriever_logger") as mock_create_retriever_logger,\
        patch("src.handlers.create_flow_logger") as mock_create_flow_logger,\
            patch("src.handlers.create_language_logger") as mock_create_language_logger, \
            patch("src.handlers.create_channel_logger") as mock_create_channel_logger,\
                patch("src.handlers.create_api_logger") as mock_create_api_logger:
        
        await logging_data_into_db(service_name="invalid_service",input_data=None)
        mock_create_retriever_logger.assert_not_called()
        mock_create_flow_logger.assert_not_called()
        mock_create_language_logger.assert_not_called()
        mock_create_channel_logger.assert_not_called()
        mock_create_api_logger.assert_not_called()