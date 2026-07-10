# backend/app/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:fallback@localhost:5432/postgres")
    PROJECT_NAME: str = "AgroLink AI Enterprise Engine Gateway"
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    MODEL_PATH: str = os.path.join(BASE_DIR, "ml_models", "cinnamon_model.pkl")

settings = Settings()