import os
from typing import Union, Optional
from datetime import timedelta
import logging
from google.cloud import storage

logger = logging.getLogger("storage")

class GcpSyncStorage:
    __client__ = None
    tmp_folder = "/tmp/jb_files"

    def __init__(self):
        logger.info("Initializing GCP Storage")

        project_id = 'indian-legal-bert'
        self.__bucket_name__ = 'jugalbandi'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/sunandhitab/Downloads/indian-legal-bert-72a5c6f931f1.json'

        if not project_id or not self.__bucket_name__:
            raise ValueError(
                "GCPStorage client not initialized. Missing project_id or bucket_name"
            )

        self.__client__ = storage.Client(project=project_id)
        os.makedirs(self.tmp_folder, exist_ok=True)

    def write_file(
        self,
        file_path: str,
        file_content: Union[str, bytes],
        mime_type: Optional[str] = None,
    ):
        if not self.__client__:
            raise Exception("GCPStorage client not initialized")

        blob_name = file_path
        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(blob_name)

        if mime_type is None:
            mime_type = (
                "audio/mpeg" if file_path.lower().endswith(".mp3") else "application/octet-stream"
            )

        # Use synchronous method to upload
        blob.upload_from_string(file_content, content_type=mime_type)

    def download_file_to_temp_storage(
        self, file_path: Union[str, os.PathLike]
    ) -> Union[str, os.PathLike]:
        if not self.__client__:
            raise Exception("GCPStorage client not initialized")

        blob_name = file_path
        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(blob_name)

        tmp_file_path = os.path.join(self.tmp_folder, file_path)
        os.makedirs(os.path.dirname(tmp_file_path), exist_ok=True)

        # Download the file to the temporary location
        with open(tmp_file_path, 'wb') as my_blob:
            blob.download_to_file(my_blob)

        return tmp_file_path

    def public_url(self, file_path: str) -> str:
        if not self.__client__:
            raise Exception("GCPStorage client not initialized")

        blob_name = file_path
        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(blob_name)

        return blob.generate_signed_url(
            version="v4",
            expiration=timedelta(days=1),
            method="GET"
        )

# Example usage
def main():
    storage = GcpSyncStorage()
    storage.write_file('example.txt', 'Hello, World!')
    tmp_path = storage.download_file_to_temp_storage('example.txt')
    print(f"File downloaded to: {tmp_path}")
    url = storage.public_url('example.txt')
    print(f"Public URL: {url}")

if __name__ == "__main__":
    main()
