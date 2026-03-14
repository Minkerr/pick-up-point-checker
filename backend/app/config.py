from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    nominatim_user_agent: str = "pick-up-point-checker/1.0"
    cors_origins: str = "http://localhost:8080,http://127.0.0.1:8080"
    ozon_cookie: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
