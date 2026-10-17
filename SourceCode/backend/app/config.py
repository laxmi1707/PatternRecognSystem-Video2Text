from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Video2Knowledge API"
    app_version: str = "0.2.0"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/video2knowledge"
    upload_dir: str = "./uploads"
    dataset_root: str = "./dataset"

    # Model artifacts: downloaded from S3 at startup, then loaded from the local
    # model directory (which is also the fallback on any S3 failure).
    # Set MODEL_S3_BUCKET to an empty string to skip S3 and use local models only.
    model_s3_bucket: str | None = "video2knowledge-dev-model-artifacts-984263476980"
    model_s3_prefix: str = "models/v1"
    model_s3_region: str | None = "ap-southeast-1"
    model_s3_require_checksum: bool = False

    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type"]
    allow_credentials: bool = True


settings = Settings()
