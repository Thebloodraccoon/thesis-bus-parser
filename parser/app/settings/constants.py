from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_HOST: str
    POSTGRES_PORT: str
    POSTGRES_DB: str

    @computed_field
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Test database settings
    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: SecretStr
    TEST_POSTGRES_HOST: str
    TEST_POSTGRES_PORT: str
    TEST_POSTGRES_DB: str

    @computed_field
    def TEST_DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.TEST_POSTGRES_USER}:{self.TEST_POSTGRES_PASSWORD.get_secret_value()}"
            f"@{self.TEST_POSTGRES_HOST}:5432/{self.TEST_POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: SecretStr

    @computed_field
    def REDIS_URL(self) -> str:
        return (
            f"redis://:{self.REDIS_PASSWORD.get_secret_value()}"
            f"@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        )

    # Pushgateway
    PUSHGATEWAY_HOST: str
    PUSHGATEWAY_PORT: str

    @computed_field
    def PUSHGATEWAY_URL(self) -> str:
        return f"http://{self.PUSHGATEWAY_HOST}:{self.PUSHGATEWAY_PORT}"

    API_KEY: str

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "allow"}


settings = Settings()  # type: ignore
