"""Application settings and environment configurations."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings configuration loaded from environment variables or .env file."""

    APP_NAME: str = "ACTUS Financial Contract Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # MST Blockchain Configuration
    MST_RPC_URL: str = "https://testnetrpc.mstblockchain.com"
    MST_CHAIN_ID: int = 91562037
    MST_PRIVATE_KEY: str | None = None
    MST_CONTRACT_ADDRESS: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
