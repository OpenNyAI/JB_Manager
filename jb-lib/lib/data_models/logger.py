from pydantic import BaseModel
from typing import Union, List

class APILogger(BaseModel):
    user_id: str
    turn_id: str
    session_id: str
    status: str

class ChannelLogger(BaseModel):
    id: str
    turn_id: str
    channel_id: str
    channel_name: str
    msg_intent: str
    msg_type: str
    sent_to_service: str
    status: str

class LanguageLogger(BaseModel):
    id : str
    turn_id : str
    msg_id : str
    msg_state : str
    msg_language : str
    msg_type : str
    translated_to_language : str
    translation_type : str
    translation_model : str
    response_time : str
    status : str

class FlowLogger(BaseModel):
    id :str
    turn_id :str
    session_id :str
    msg_id :str
    msg_intent :str
    flow_intent :str
    sent_to_service :str
    status :str

class RetrieverLogger(BaseModel):
    id :str
    turn_id :str
    msg_id :str
    retriever_type :str
    collection_name :str
    top_chunk_k_value :str
    number_of_chunks :str
    chunks :List[str]
    query :str
    status :str

class Logger(BaseModel):
    source: str
    logger_obj: Union[APILogger, ChannelLogger, LanguageLogger, FlowLogger, RetrieverLogger]