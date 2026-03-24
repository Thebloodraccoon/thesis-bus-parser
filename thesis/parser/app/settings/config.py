from thesis.core.config import CoreSettings


class Settings(CoreSettings):
    API_KEY: str = ""
    model_config = {"env_file": ".env", "extra": "allow"}


settings = Settings()
