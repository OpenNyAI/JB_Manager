import os
from typing import Union, Optional
from datetime import datetime, timedelta, timezone
import logging
from google.cloud import storage
import aiofiles

logger = logging.getLogger("storage")

class GcpAsyncStorage:
    __client__ = None
    tmp_folder = "/tmp/jb_files"

    def __init__(self):
        logger.info("Initializing GCP Storage")
        
        project_id = 'indian-legal-bert'
        self.__bucket_name__ = 'jugalbandi'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/sunandhitab/Downloads/indian-legal-bert-72a5c6f931f1.json'
        if not project_id or not self.__bucket_name__:
            print(project_id, self.__bucket_name__)
            raise ValueError(
                "GCPAsyncStorage client not initialized. Missing project_id or bucket_name"
            )

        self.__client__ = storage.Client(project=project_id)
        os.makedirs(self.tmp_folder, exist_ok=True)

    async def write_file(
        self,
        file_path: str,
        file_content: Union[str, bytes],
        mime_type: Optional[str] = None,
    ):
        if not self.__client__:
            raise Exception("GCPAsyncStorage client not initialized")

        blob_name = file_path
        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(blob_name)

        # Determine MIME type if not provided
        if mime_type is None:
            mime_type = (
                "audio/mpeg" if file_path.lower().endswith(".mp3") else "application/octet-stream"
            )

        # Upload the blob
        await asyncio.to_thread(blob.upload_from_string, file_content, content_type=mime_type)

    async def _download_file_to_temp_storage(
        self, file_path: Union[str, os.PathLike]
    ) -> Union[str, os.PathLike]:
        if not self.__client__:
            raise Exception("GCPAsyncStorage client not initialized")

        blob_name = file_path
        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(blob_name)

        tmp_file_path = os.path.join(self.tmp_folder, file_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)

        async with aiofiles.open(tmp_file_path, 'wb') as my_blob:
            await asyncio.to_thread(blob.download_to_file, my_blob)

        return tmp_file_path

    def public_url(self, file_path: str) -> str:
        if not self.__client__:
            raise Exception("GCPAsyncStorage client not initialized")

        blob_name = file_path
        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(blob_name)

        # Generate a signed URL that expires in 1 day
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=1),
            method="GET"
        )

        return url

# Example usage
async def main():
    storage = GcpAsyncStorage()
    await storage.write_file('example.txt', 'Hello, World!')
    tmp_path = await storage._download_file_to_temp_storage('example.txt')
    print(f"File downloaded to: {tmp_path}")
    url = storage.public_url('example.txt')
    print(f"Public URL: {url}")

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())