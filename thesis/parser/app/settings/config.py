from typing import Optional
from thesis.core.config import CoreSettings


class Settings(CoreSettings):
    API_KEY: str = ""
    PROXY_URL: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
