from minio import Minio
from ..config import settings
import logging
import os

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
            logger.info(f"Created bucket {self.bucket_name}")

    def download_file(self, object_name: str, file_path: str):
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
            logger.info(f"Downloaded {object_name} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {object_name}: {e}")
            raise e

    def upload_file(self, object_name: str, file_path: str, content_type: str):
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            logger.info(f"Uploaded {object_name} to {self.bucket_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {object_name}: {e}")
            raise e

storage = StorageService()
