from minio import Minio
from ..config import settings
import logging
import os
import io

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

    def get_object_stream(self, object_name: str):
        try:
            return self.client.get_object(self.bucket_name, object_name)
        except Exception as e:
            logger.error(f"Failed to get object stream {object_name}: {e}")
            raise e
            
    def list_objects(self, prefix: str, recursive: bool = True):
        return self.client.list_objects(self.bucket_name, prefix=prefix, recursive=recursive)

    def remove_object(self, object_name: str):
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Removed object {object_name}")
        except Exception as e:
            logger.error(f"Failed to remove object {object_name}: {e}")

storage = StorageService()
