from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "videos"
    
    WHISPER_MODEL_SIZE: str = "base"  # default to base for faster local testing
    WHISPER_DEVICE: str = "cpu"       # default to cpu
    WHISPER_COMPUTE_TYPE: str = "int8" # efficient default

settings = Settings()
