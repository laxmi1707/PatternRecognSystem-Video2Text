from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Video2Knowledge API"
    app_version: str = "0.2.0"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./video2text.db"
    upload_dir: str = "./uploads"
    dataset_root: str = "./dataset"

    allowed_origins: list[str] = ["http://localhost:5173"]
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type"]
    allow_credentials: bool = True


settings = Settings()
