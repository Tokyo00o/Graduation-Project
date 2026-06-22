from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "FuzzGuard API"
    database_url: str = "sqlite:///./fuzzguard.db"
    debug: bool = True
    scheduler_enabled: bool = True
    scheduler_check_interval: int = 30
    jwt_secret: str = "fuzzguard-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24h

    # Observability
    log_level: str = "INFO"
    log_json: bool = True
    metrics_enabled: bool = True
    tracing_enabled: bool = False
    tracing_otlp_endpoint: str = ""
    tracing_console: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
