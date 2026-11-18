import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "IncuBrix Long-Tail Distribution Service"
    API_V1_PREFIX: str = "/api/v1"
    CONNECTOR_PREFIX: str = "/connector/v1"
    LOG_LEVEL: str = "INFO"
    SIMULATION_MODE: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()