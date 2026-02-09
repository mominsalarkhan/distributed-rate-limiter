from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    rate_limit_requests: int = 100  # requests per window
    rate_limit_window: int = 60     # window in seconds
    
    class Config:
        env_file = ".env"

settings = Settings()