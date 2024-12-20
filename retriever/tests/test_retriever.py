import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from lib.data_models import Logger,RetrieverLogger

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("KAFKA_BROKER", "kafka:9092")
    monkeypatch.setenv("KAFKA_RETRIEVER_TOPIC", "retriever_topic")
    monkeypatch.setenv("KAFKA_FLOW_TOPIC", "flow_topic")
    monkeypatch.setenv("KAFKA_LOGGER_TOPIC", "logger_topic")
    monkeypatch.setenv("POSTGRES_DATABASE_NAME", "test_db")
    monkeypatch.setenv("POSTGRES_DATABASE_USERNAME", "test_user")
    monkeypatch.setenv("POSTGRES_DATABASE_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_DATABASE_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DATABASE_PORT", "5432")

@pytest.mark.asyncio
async def test_r2r_querying():
    from main import querying

    mock_r2r_app = MagicMock()
    mock_search_result = {"vector_search_results": [{"metadata": {"text": "test"}}]}
    mock_r2r_app.engine.asearch = AsyncMock(return_value=mock_search_result)

    retriever_logger_object= Logger(
        source = "retriever",
        logger_obj = RetrieverLogger(
            id = "1234",
            turn_id = "turn_id",
            msg_id = "abcd",
            retriever_type = "r2r",
            collection_name = "collection_name",
            top_chunk_k_value= "5",
            number_of_chunks = "400",
            chunks = ["chunk1", "chunk2"],
            query = "query",
            status = "Success",
        )
    )
    
    with patch("main.get_r2r", return_value=mock_r2r_app), patch(
        "main.send_message", MagicMock()
    ) as mock_send_message, patch("main.create_retriever_logger_input", return_value=retriever_logger_object):
        await querying(
            type="r2r",
            turn_id="turn_id",
            collection_name="collection_name",
            query="query",
            metadata=None,
            callback=mock_send_message,
        )
        mock_r2r_app.engine.asearch.assert_called_once()
        mock_send_message.assert_called_once()


@pytest.mark.asyncio
async def test_default_querying():
    from main import querying

    mock_pgvector_instance = MagicMock()
    mock_documents = [MagicMock(page_content="test_content", metadata={"key": "value"})]
    mock_pgvector_instance.similarity_search = MagicMock(return_value=mock_documents)

    retriever_logger_object= Logger(
        source = "retriever",
        logger_obj = RetrieverLogger(
            id = "1234",
            turn_id = "turn_id",
            msg_id = "abcd",
            retriever_type = "default",
            collection_name = "collection_name",
            top_chunk_k_value= "5",
            number_of_chunks = "400",
            chunks = ["chunk1", "chunk2"],
            query = "query",
            status = "Success",
        )
    )

    with patch("main.PGVector", return_value=mock_pgvector_instance), patch(
        "main.get_embeddings", return_value=MagicMock()
    ), patch("main.send_message", MagicMock()) as mock_send_message, patch("main.create_retriever_logger_input", return_value=retriever_logger_object):
        await querying(
            type="default",
            turn_id="turn_id",
            collection_name="collection_name",
            query="query",
            metadata=None,
            callback=mock_send_message,
        )
        mock_pgvector_instance.similarity_search.assert_called_once()
        mock_send_message.assert_called_once()


@patch("main.R2R")
def test_get_r2r(mock_r2r):
    from main import get_r2r

    instance = get_r2r()
    assert instance == mock_r2r.return_value


@patch("main.AzureOpenAIEmbeddings")
@patch("main.OpenAIEmbeddings")
def test_get_embeddings(mock_openai_embeddings, mock_azure_openai_embeddings):
    from main import get_embeddings

    os.environ["OPENAI_API_TYPE"] = "azure"
    instance = get_embeddings()
    assert instance == mock_azure_openai_embeddings.return_value

    os.environ["OPENAI_API_TYPE"] = "openai"
    instance = get_embeddings()
    assert instance == mock_openai_embeddings.return_value
