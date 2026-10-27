"""Configuração lida de variáveis de ambiente (nunca de valores fixos no código)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# O .env fica na raiz do monorepo, não em apps/api. Na hospedagem o arquivo não
# existe e as variáveis vêm do ambiente.
ROOT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    app_env: Literal["development", "staging", "production"] = "development"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def supabase_configured(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)


@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=ROOT_ENV_FILE)
