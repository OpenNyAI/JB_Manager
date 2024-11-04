from lib.db_session_handler import DBSessionHandler
from lib.models import (
    JBApiLogger,
    JBChannelLogger,
    JBLanguageLogger,
)

async def create_api_logger(
    msg_id: str, user_id: str, turn_id: str, session_id: str, status: str, 
) -> JBApiLogger:
    api_logger_data = JBApiLogger(
        msg_id = msg_id,
        user_id = user_id,
        turn_id = turn_id,
        session_id = session_id, 
        status = status,
    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(api_logger_data)
            await session.commit()
            return api_logger_data
    return None

async def create_channel_logger(
        id: str, 
        turn_id: str, 
        channel_id: str, 
        channel_name: str, 
        msg_intent: str, 
        msg_type: str, 
        sent_to_service: str, 
        status: str) -> JBChannelLogger:
    channel_logger_data = JBChannelLogger(
                    id = id,
                    turn_id = turn_id,
                    channel_id = channel_id,
                    channel_name = channel_name,
                    msg_intent = msg_intent,
                    msg_type = msg_type,
                    sent_to_service = sent_to_service,
                    status = status
                    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(channel_logger_data)
            await session.commit()
            return channel_logger_data
    return None
    
async def create_language_logger(
        id : str,
        turn_id : str,
        msg_id : str,
        msg_state : str,
        msg_language : str,
        msg_type : str,
        translated_to_language : str,
        translation_type : str,
        translation_model : str,
        response_time : str,
        status : str) -> JBLanguageLogger:
     
    language_logger_data = JBLanguageLogger(
                    id = id,
                    turn_id = turn_id,
                    msg_id = msg_id,
                    msg_state = msg_state,
                    msg_language = msg_language,
                    msg_type = msg_type,
                    translated_to_language = translated_to_language,
                    translation_type = translation_type,
                    model_for_translation = translation_model,
                    response_time = response_time,
                    status = status
                    )
    async with DBSessionHandler.get_async_session() as session:
        async with session.begin():
            session.add(language_logger_data)
            await session.commit()
            return language_logger_data
    return None