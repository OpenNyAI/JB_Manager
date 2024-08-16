import os
from typing import Union, Optional
from datetime import datetime, timedelta, timezone
import logging
from google.cloud import storage
from ..storage import SyncStorage

logger = logging.getLogger("storage")


class GCPSyncStorage(SyncStorage):
    __client__ = None
    tmp_folder = "/tmp/jb_files"

    def __init__(self):
        logger.info("Initializing GCP Storage") 
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        if not bucket_name:
            raise ValueError(
                "GCPAsyncStorage client not initialized. Missing bucket_name ")
        self.__bucket_name__ = bucket_name
        self.__client__ = storage.Client()
        os.makedirs(self.tmp_folder, exist_ok=True)


    def write_file(
        self,
        file_path: str,
        file_content: Union[str, bytes],
        mime_type: Optional[str] = None,
    ):
        if not self.__client__:
            raise Exception("GCPSyncStorage client not initialized")

        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(file_path)

        if mime_type is None:
            mime_type = (
                "audio/mpeg"
                if file_path.lower().endswith(".mp3")
                else "application/octet-stream"
            )
        blob.upload_from_string(file_content, content_type=mime_type)


    def _download_file_to_temp_storage(
        self, file_path: Union[str, os.PathLike]
    ) -> Union[str, os.PathLike]:
        if not self.__client__:
            raise Exception("GCPSyncStorage client not initialized")

        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(file_path)

        tmp_file_path = os.path.join(self.tmp_folder, file_path)
        blob.download_to_filename(tmp_file_path)
        return tmp_file_path

    def public_url(self, file_path: str) -> str:
        if not self.__client__:
            raise Exception("GCPSyncStorage client not initialized")

        bucket = self.__client__.bucket(self.__bucket_name__)
        blob = bucket.blob(file_path)

        url = blob.generate_signed_url(expiration=timedelta(days=1))
        return url
