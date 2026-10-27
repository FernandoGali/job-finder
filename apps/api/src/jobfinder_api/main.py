"""Ponto de entrada da API do Job Finder."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jobfinder_api import __version__
from jobfinder_api.auth import CurrentUser, get_current_user
from jobfinder_api.config import Settings, get_settings


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    supabase_configured: bool


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Job Finder API", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse)
    def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
        """Diz se a API está no ar. Nunca expõe valores de chaves, só se existem."""
        return HealthResponse(
            status="ok",
            version=__version__,
            env=settings.app_env,
            supabase_configured=settings.supabase_configured,
        )

    @app.get("/me", response_model=CurrentUser)
    def me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        """Quem está logado, segundo o token enviado. Exige login."""
        return user

    return app


app = create_app()
