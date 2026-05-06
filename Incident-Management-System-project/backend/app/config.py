from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_url: str = "postgresql+asyncpg://ims_user:ims_pass@postgres:5432/ims_db"
    mongo_url: str = "mongodb://mongo:27017"
    mongo_db: str = "ims_signals"
    redis_url: str = "redis://redis:6379"
    app_name: str = "Incident Management System"
    debug: bool = False
    rate_limit_per_minute: int = 600
    debounce_window_seconds: int = 10
    debounce_threshold: int = 100
    metrics_interval_seconds: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
