import asyncio
import json
import logging
import os
import sys
import traceback
import uuid

from dotenv import load_dotenv
from langchain_community.vectorstores import PGVector
from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings
from lib.data_models import RAG, Flow, Logger, RetrieverLogger
from lib.kafka_utils import KafkaConsumer, KafkaProducer
from r2r import R2R, VectorSearchSettings
from typing import List

from crud import get_msg_id_by_turn_id

load_dotenv()

print("Inside Retriever", file=sys.stderr)

kafka_broker = os.getenv("KAFKA_BROKER")
retriever_topic = os.getenv("KAFKA_RETRIEVER_TOPIC")
flow_topic = os.getenv("KAFKA_FLOW_TOPIC")
logger_topic = os.getenv("KAFKA_LOGGER_TOPIC")

print("Connecting", file=sys.stderr)

consumer = KafkaConsumer.from_env_vars(
    group_id="cooler_group_id", auto_offset_reset="latest"
)
producer = KafkaProducer.from_env_vars()

print("Connections done", file=sys.stderr)

logger = logging.getLogger("retriever")

db_name = os.getenv("POSTGRES_DATABASE_NAME")
db_user = os.getenv("POSTGRES_DATABASE_USERNAME")
db_password = os.getenv("POSTGRES_DATABASE_PASSWORD")
db_host = os.getenv("POSTGRES_DATABASE_HOST")
db_port = os.getenv("POSTGRES_DATABASE_PORT")
db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
os.environ["POSTGRES_DBNAME"] = db_name
os.environ["POSTGRES_USER"] = db_user
os.environ["POSTGRES_PASSWORD"] = db_password
os.environ["POSTGRES_HOST"] = db_host
os.environ["POSTGRES_PORT"] = db_port


def get_r2r():
    return R2R()


def get_embeddings():
    if os.getenv("OPENAI_API_TYPE") == "azure":
        return AzureOpenAIEmbeddings(
            model=os.getenv("AZURE_EMBEDDING_MODEL_NAME"),
            dimensions=1536,  # Default dimension size
            azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            openai_api_type=os.getenv("OPENAI_API_TYPE"),
            openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        )
    return OpenAIEmbeddings(client="")


def send_message(data):
    producer.send_message(flow_topic, data)

async def create_retriever_logger_input(
        turn_id :str,
        retriever_type :str,
        collection_name :str,
        top_chunk_k_value :str,
        number_of_chunks :str,
        chunks :List[str],
        query :str,
        status :str):

    id = str(uuid.uuid4())
    msg_id = await get_msg_id_by_turn_id(turn_id = turn_id)
    if msg_id is None :
        msg_id = ""
    retriever_logger_input = Logger(
        source = "retriever",
        logger_obj = RetrieverLogger(
            id = id,
            turn_id = turn_id,
            msg_id = msg_id,
            retriever_type = retriever_type,
            collection_name = collection_name,
            top_chunk_k_value= top_chunk_k_value,
            number_of_chunks = number_of_chunks,
            chunks = chunks,
            query = query,
            status = status,
        )
    )
    return retriever_logger_input


async def querying(
    type: str,
    turn_id: str,
    collection_name: str,
    query: str,
    top_chunk_k_value: int = 5,
    do_hybrid_search: bool = False,
    metadata: dict = None,
    callback: callable = None,
):
    top_k_chunks = []
    number_of_chunks: int
    if type == "r2r":
        os.environ["POSTGRES_VECS_COLLECTION"] = collection_name
        r2r_app = get_r2r()
        vector_search_settings = (
            VectorSearchSettings(
                search_filters=metadata,
                search_limit=top_chunk_k_value,
                do_hybrid_search=do_hybrid_search,
            )
            if metadata
            else VectorSearchSettings(
                search_limit=top_chunk_k_value, do_hybrid_search=do_hybrid_search
            )
        )
        search_results = await r2r_app.engine.asearch(
            query=query,
            vector_search_settings=vector_search_settings,
        )
        data = []
        for chunk in search_results["vector_search_results"][:5]:
            chunk_text = chunk["metadata"].pop("text", None)
            data.append({"chunk": chunk_text, "metadata": chunk["metadata"]})
            top_k_chunks.append(str(chunk_text))
        number_of_chunks = len(data)
    else:
        embeddings = get_embeddings()
        search_index = PGVector(
            collection_name=collection_name,
            connection_string=db_url,
            embedding_function=embeddings,
        )
        documents = (
            search_index.similarity_search(
                query=query, k=top_chunk_k_value, filter=metadata
            )
            if metadata
            else search_index.similarity_search(query=query, k=top_chunk_k_value)
        )
        data = [
            {"chunk": document.page_content, "metadata": document.metadata}
            for document in documents
        ]
        number_of_chunks = len(data)
        for document in documents:
            top_k_chunks.append(str(document.page_content))
    flow_input = {
        "source": "retriever",
        "intent": "callback",
        "callback": {"turn_id": turn_id, "callback_type": "rag", "rag_response": data},
    }
    flow_input = Flow(**flow_input)
    flow_output_data = flow_input.model_dump_json()
    if flow_output_data:
        status = "Success"
    else:
        status = "Flow output object not created"
    retriever_logger_object = await create_retriever_logger_input(
        turn_id = turn_id,
        retriever_type = type,
        collection_name = collection_name,
        top_chunk_k_value = str(top_chunk_k_value),
        number_of_chunks = str(number_of_chunks),
        chunks = top_k_chunks,
        query = query,
        status = status
    )
    producer.send_message(logger_topic, retriever_logger_object.model_dump_json(exclude_none=True))
    if callback:
        callback(flow_output_data)


async def start_retriever():
    """Starts the retriever server"""
    logger.info("Starting Listening")
    while True:
        try:
            # will keep trying until non-null message is received
            message = consumer.receive_message(retriever_topic, timeout=1.0)
            data = json.loads(message)
            data = RAG(**data)
            retriever_input = data.model_dump(
                include={
                    "type",
                    "turn_id",
                    "collection_name",
                    "query",
                    "top_chunk_k_value",
                    "do_hybrid_search",
                }
            )
            await querying(**retriever_input, callback=send_message)
        except Exception as e:
            logger.error("Exception %s :: %s", e, traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(start_retriever())
