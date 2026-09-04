from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "video2Text API"
    app_version: str = "0.1.0"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./video2text.db"

    # Pydantic-settings v2 safely evaluates mutable list literals directly.
    allowed_origins: list[str] = ["http://localhost:5173"]
    allowed_methods: list[str] = ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    allowed_headers: list[str] = ["Authorization", "Content-Type"]
    allow_credentials: bool = True

    # Optional local folder of app/<task_id>/video2knowledge_labels.jsonl documents
    # to build the search index from. None (the default) means Search returns no
    # results -- there's no shared corpus checked into the repo yet.
    search_corpus_dir: str | None = None


settings = Settings()
