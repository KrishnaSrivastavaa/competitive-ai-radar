import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    bright_data_api_key: str | None
    bright_data_api_base_url: str
    bright_data_timeout_seconds: float
    bright_data_poll_interval_seconds: float
    bright_data_poll_timeout_seconds: float
    bright_data_cli_command: str
    bright_data_cli_timeout_seconds: int


def get_settings() -> Settings:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    return Settings(
        app_name=os.getenv("APP_NAME", "Competitive AI Radar API"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./competitive_ai_radar.db"),
        bright_data_api_key=os.getenv("BRIGHT_DATA_API_KEY"),
        bright_data_api_base_url=os.getenv("BRIGHT_DATA_API_BASE_URL", "https://api.brightdata.com"),
        bright_data_timeout_seconds=float(os.getenv("BRIGHT_DATA_TIMEOUT_SECONDS", "30")),
        bright_data_poll_interval_seconds=float(os.getenv("BRIGHT_DATA_POLL_INTERVAL_SECONDS", "5")),
        bright_data_poll_timeout_seconds=float(os.getenv("BRIGHT_DATA_POLL_TIMEOUT_SECONDS", "300")),
        bright_data_cli_command=os.getenv("BRIGHT_DATA_CLI_COMMAND", "brightdata"),
        bright_data_cli_timeout_seconds=int(os.getenv("BRIGHT_DATA_CLI_TIMEOUT_SECONDS", "600")),
    )


settings = get_settings()
