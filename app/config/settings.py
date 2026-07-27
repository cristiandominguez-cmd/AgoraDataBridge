from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SOURCE_SERVER: str
    SOURCE_INSTANCE: str
    SOURCE_DATABASE: str
    SOURCE_USER: str
    SOURCE_PASSWORD: str

    AGORA_SERVER: str
    AGORA_INSTANCE: str
    AGORA_DATABASE: str
    AGORA_USER: str
    AGORA_PASSWORD: str

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
