from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "videos"
    
    DEFAULT_RATIO: str = "9:16"
    DEFAULT_SUB_STYLE: str = "hormozi"

settings = Settings()
