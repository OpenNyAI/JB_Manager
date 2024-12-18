import json
import os
from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, MagicMock, mock_open, patch
from r2r import ChunkingConfig, R2RBuilder, R2RConfig
import asyncpg
import pytest
from lib.data_models import Indexer
from model import InternalServerException


# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("POSTGRES_DATABASE_NAME", "test_db")
    monkeypatch.setenv("POSTGRES_DATABASE_USERNAME", "test_user")
    monkeypatch.setenv("POSTGRES_DATABASE_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_DATABASE_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DATABASE_PORT", "5432")


# Mock read_file function
@asynccontextmanager
async def mock_read_file(file_path, mode):
    mock_file = MagicMock()
    mock_file.read = AsyncMock(return_value=b"test content")
    mock_file.name = "temp_test.txt"
    yield mock_file


# Mock storage instance
mock_storage_instance = MagicMock()
mock_storage_instance.read_file = mock_read_file


# Patching the StorageHandler in lib.file_storage with the mock
with patch(
    "lib.file_storage.StorageHandler.get_async_instance",
    return_value=mock_storage_instance,
):
    import indexing

    def test_parse_file():
        # Mock parser functions
        with patch("indexing.pdf_parser", return_value="PDF Content") as mock_pdf_parser, \
            patch("indexing.docx_parser", return_value="DOCX Content") as mock_docx_parser, \
            patch("indexing.xlsx_parser", return_value="XLSX Content") as mock_xlsx_parser, \
            patch("indexing.json_parser", return_value="JSON Content") as mock_json_parser, \
            patch("indexing.default_parser", return_value="Default Content") as mock_default_parser:

            # Test PDF file
            result = indexing.parse_file("test.pdf")
            assert result == "PDF Content"
            mock_pdf_parser.assert_called_once_with("test.pdf")

            # Test DOCX file
            result = indexing.parse_file("test.docx")
            assert result == "DOCX Content"
            mock_docx_parser.assert_called_once_with("test.docx")

            # Test XLSX file
            result = indexing.parse_file("test.xlsx")
            assert result == "XLSX Content"
            mock_xlsx_parser.assert_called_once_with("test.xlsx")

            # Test JSON file
            result = indexing.parse_file("test.json")
            assert result == "JSON Content"
            mock_json_parser.assert_called_once_with("test.json")

            # Test unsupported file extension (uses default parser)
            result = indexing.parse_file("test.txt")
            assert result == "Default Content"
            mock_default_parser.assert_called_once_with("test.txt")

    def test_docx_parser():
        with patch("docx2txt.process", return_value="DOCX Content") as mock_process:
            result = indexing.docx_parser("test.docx")
            assert result == "DOCX Content"
            mock_process.assert_called_once_with("test.docx")

    def test_pdf_parser():
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF Page Content"
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])
        with patch("fitz.open", return_value=mock_doc):
            result = indexing.pdf_parser("test.pdf")
            assert result == "PDF Page Content"

    def test_xlsx_parser():
        mock_df = MagicMock()
        mock_df.to_string.return_value = "XLSX Content"
        with patch("pandas.read_excel", return_value=mock_df):
            result = indexing.xlsx_parser("test.xlsx")
            assert result == "XLSX Content"
            mock_df.to_string.assert_called_once_with(index=False)

    def test_json_parser():
        mock_json_data = {"key": "value"}
        with patch("builtins.open", mock_open(read_data=json.dumps(mock_json_data))):
            result = indexing.json_parser("test.json")
            assert result == json.dumps(mock_json_data, indent=4)

    def test_default_parser():
        with patch("builtins.open", mock_open(read_data="Default Content")):
            result = indexing.default_parser("test.txt")
            assert result == "Default Content"

    # Test TextConverter.textify method
    @pytest.mark.asyncio
    async def test_text_converter_textify():
        converter = indexing.TextConverter()
        with patch("indexing.parse_file", return_value="Parsed Content"):
            result = await converter.textify("test.txt")
            assert result == "Parsed Content"

    @pytest.mark.asyncio
    async def test_create_pg_vector_index_if_not_exists():
        # Mock the asyncpg connection and its methods
        mock_connection = MagicMock(spec=asyncpg.connection.Connection)

        with patch("asyncpg.connect", return_value=mock_connection):
            # Initialize the DataIndexer instance
            indexer = indexing.DataIndexer()

            # Call the method
            await indexer.create_pg_vector_index_if_not_exists()

            # Assertions
            mock_connection.transaction.assert_called_once()
            mock_connection.execute.assert_any_call(
                "ALTER TABLE langchain_pg_embedding ALTER COLUMN embedding TYPE vector(1536)"
            )
            mock_connection.execute.assert_any_call(
                "CREATE INDEX IF NOT EXISTS langchain_embeddings_hnsw ON langchain_pg_embedding USING hnsw (embedding vector_cosine_ops)"
            )
            mock_connection.close.assert_called_once()

    # Test DataIndexer.index method for default input
    @pytest.mark.asyncio
    async def test_default_data_indexer():
        indexer = indexing.DataIndexer()
        indexer_input = Indexer(
            files=["test.txt"],
            collection_name="test_collection",
            type="default",
            chunk_size=2000,
            chunk_overlap=100,
        )
        with patch.object(
            indexer.text_converter,
            "textify",
            AsyncMock(return_value="File Content"),
        ), patch.object(
            indexer, "get_embeddings", AsyncMock()
        ), patch.object(
            indexer, "create_pg_vector_index_if_not_exists", AsyncMock()
        ), patch(
            "langchain_community.vectorstores.PGVector.from_documents", MagicMock()
        ) as mock_pg_vector:
            await indexer.index(indexer_input)
            mock_pg_vector.assert_called_once()
            indexer.create_pg_vector_index_if_not_exists.assert_awaited_once()
    
    @pytest.mark.asyncio
    async def test_get_r2r():
        indexer = indexing.DataIndexer()
        chunk_size = 4000
        chunk_overlap = 200
        mock_r2r_app = MagicMock()

        with patch("indexing.R2RConfig") as MockR2RConfig, patch("indexing.R2RBuilder") as MockR2RBuilder:
            mock_r2r_builder = MagicMock()
            MockR2RBuilder.return_value = mock_r2r_builder
            mock_r2r_builder.build.return_value = mock_r2r_app

            r2r_app = await indexer.get_r2r(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

            MockR2RConfig.assert_called_once_with(
                config_data={
                    "chunking": ChunkingConfig(
                        chunk_size=chunk_size, chunk_overlap=chunk_overlap
                    ),
                }
            )

            MockR2RBuilder.assert_called_once_with(config=MockR2RConfig.return_value)
            mock_r2r_builder.build.assert_called_once()

            assert r2r_app == mock_r2r_app

    # Test DataIndexer.index method for r2r input
    @pytest.mark.asyncio
    async def test_r2r_data_indexer():
        indexer = indexing.DataIndexer()
        indexer_input = Indexer(
            files=["test.txt"],
            collection_name="test_collection",
            type="r2r",
            chunk_size=4000,
            chunk_overlap=200,
        )
        mock_r2r_app = MagicMock()
        mock_r2r_app.engine.aingest_files = AsyncMock()

        with patch.object(indexer, "get_r2r", return_value=mock_r2r_app):
            await indexer.index(indexer_input)
            mock_r2r_app.engine.aingest_files.assert_awaited_once_with(files=[ANY])
            assert os.environ["POSTGRES_VECS_COLLECTION"] == "test_collection"

    @pytest.mark.asyncio
    async def test_get_embeddings_azure():
        # Mock environment variables for Azure setup
        os.environ["OPENAI_API_TYPE"] = "azure"
        os.environ["AZURE_EMBEDDING_MODEL_NAME"] = "azure-model-name"
        os.environ["AZURE_DEPLOYMENT_NAME"] = "azure-deployment"
        os.environ["AZURE_OPENAI_ENDPOINT"] = "https://azure-endpoint"
        os.environ["AZURE_OPENAI_API_KEY"] = "azure-api-key"

        indexer = indexing.DataIndexer()

        # Mock the AzureOpenAIEmbeddings class and its constructor
        with patch("indexing.AzureOpenAIEmbeddings") as mock_azure_embeddings:
            mock_instance = MagicMock()
            mock_azure_embeddings.return_value = mock_instance

            # Call the get_embeddings method
            embeddings = await indexer.get_embeddings()

            # Assert that AzureOpenAIEmbeddings was created with the correct parameters
            mock_azure_embeddings.assert_called_once_with(
                model="azure-model-name",
                dimensions=1536,
                azure_deployment="azure-deployment",
                azure_endpoint="https://azure-endpoint",
                openai_api_type="azure",
                openai_api_key="azure-api-key"
            )

            # Assert the returned value is the mocked instance of AzureOpenAIEmbeddings
            assert embeddings == mock_instance


    @pytest.mark.asyncio
    async def test_get_embeddings_openai():
        # Mock environment variables for OpenAI setup
        os.environ["OPENAI_API_TYPE"] = "openai"
        
        indexer = indexing.DataIndexer()

        # Mock the OpenAIEmbeddings class and its constructor
        with patch("indexing.OpenAIEmbeddings") as mock_openai_embeddings:
            mock_instance = MagicMock()
            mock_openai_embeddings.return_value = mock_instance

            # Call the get_embeddings method
            embeddings = await indexer.get_embeddings()

            # Assert that OpenAIEmbeddings was created with the correct parameters
            mock_openai_embeddings.assert_called_once_with(client="")

            # Assert the returned value is the mocked instance of OpenAIEmbeddings
            assert embeddings == mock_instance

