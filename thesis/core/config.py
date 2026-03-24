from pydantic import SecretStr, computed_field
from pydantic_settings import BaseSettings

class CoreSettings(BaseSettings):
    DATABASE_USER: str
    DATABASE_PASSWORD: SecretStr
    DATABASE_HOST: str
    DATABASE_PORT: str
    DATABASE_DB: str

    @computed_field
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD.get_secret_value()}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_DB}"
        )

    REDIS_HOST: str
    REDIS_PORT: str
    REDIS_PASSWORD: SecretStr

    @computed_field
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD.get_secret_value()}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = {"env_file": ".env", "extra": "allow"}