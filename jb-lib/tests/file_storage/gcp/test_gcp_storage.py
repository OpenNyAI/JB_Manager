import os
import asyncio
import unittest
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from unittest import mock
from google.cloud import storage
from google.cloud.storage import Blob
from lib.file_storage.gcp.gcp_storage import GcpAsyncStorage 

class TestGCPAsyncStorage(unittest.TestCase):

    @mock.patch('google.cloud.storage.Client')
    def setUp(self, mock_storage_client):
        os.environ['GCP_PROJECT_ID'] = 'test-project-id'
        os.environ['GCP_STORAGE_BUCKET'] = 'test-bucket'

        # Initialize the GCPAsyncStorage instance
        self.storage = GcpAsyncStorage()

        # Mock the bucket and blob
        self.mock_bucket = mock_storage_client.return_value.bucket.return_value
        self.mock_blob = self.mock_bucket.blob.return_value

    @patch("google.cloud.storage.Blob")
    @pytest.mark.asyncio
    async def test_write_file(mock_blob):
        with patch("lib.file_storage.gcp.gcp_storage.os.getenv") as mock_getenv, patch("google.cloud.storage.Client") as mock_storage_client:
            mock_getenv.side_effect = lambda key: {
                "GCP_STORAGE_BUCKET_NAME": "test_bucket",
                "GCP_STORAGE_PROJECT": "fake_project",
            }.get(key, None)

            mock_storage_client_instance = MagicMock()
            mock_storage_client.return_value = mock_storage_client_instance
            
            mock_blob_instance = MagicMock(spec=Blob)
            mock_blob_instance.upload_from_string = AsyncMock()
            mock_storage_client_instance.bucket.return_value.blob.return_value = mock_blob_instance

            storage = GcpAsyncStorage()
            print("Writing file")

            await storage.write_file("test.txt", b"content")
            print("File written")

            mock_storage_client_instance.bucket.assert_called_once_with("test_bucket")
            mock_storage_client_instance.bucket.return_value.blob.assert_called_once_with("test.txt")
            mock_blob_instance.upload_from_string.assert_called_once_with(b"content")


    @mock.patch('aiofiles.open', new_callable=mock.AsyncMock)
    async def test_download_file_to_temp_storage(self, mock_aiofiles_open):
        file_path = 'test.txt'
        mock_file = mock.MagicMock()  # Mock the file object returned by aiofiles

        mock_aiofiles_open.return_value.__aenter__.return_value = mock_file

        # Set up the download method to do nothing when called
        self.mock_blob.download_to_file = mock.AsyncMock()

         # Call the async method using asyncio.run
        async def run_test():
            tmp_path = await self.storage._download_file_to_temp_storage(file_path)
            return tmp_path

        tmp_path = asyncio.run(run_test())

        # Check that the correct temporary file path was returned
        self.assertEqual(tmp_path, os.path.join(self.storage.tmp_folder, file_path))

        # Assert that the download_to_file method was called with the mock file object
        self.mock_blob.download_to_file.assert_called_once_with(mock_file)


    async def test_public_url(self):
        file_path = 'test.txt'

        url = self.storage.public_url(file_path)

        # Assert the signed URL generation was called
        self.mock_blob.generate_signed_url.assert_called_once_with(
            version="v4",
            expiration=mock.ANY,
            method="GET"
        )

        # Assert that the URL is generated correctly
        self.assertIsInstance(url, str)

    @mock.patch('os.makedirs')
    def tearDown(self, mock_makedirs):
        # Clean up any resources after tests
        pass

if __name__ == '__main__':
    unittest.main()
