"""Rota que analisa um currículo com a IA e guarda o perfil extraído."""

import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, Protocol

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.auth import UserSession, get_session
from jobfinder_api.config import Settings, get_settings
from jobfinder_api.resume_analysis import (
    AnalysisError,
    AnalysisResult,
    AnalysisUnavailableError,
    ResumeAnalyzer,
    ResumeProfile,
)
from jobfinder_api.resume_text import UnreadableResumeError, extract_text
from jobfinder_api.resumes import ResumeStore, get_resume_store
from jobfinder_api.supabase_user import SupabaseError

logger = logging.getLogger(__name__)


class Analyzer(Protocol):
    async def analyze(self, resume_text: str) -> AnalysisResult: ...


class ProfileWriter(Protocol):
    async def save_profile(self, row: dict[str, Any]) -> None: ...


async def get_analyzer(settings: Settings = Depends(get_settings)) -> AsyncIterator[Analyzer]:
    if not settings.anthropic_api_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Análise indisponível no momento.")
    async with anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key) as client:
        yield ResumeAnalyzer(client)


router = APIRouter()


@router.post("/curriculos/{resume_id}/analise", response_model=ResumeProfile)
async def analyze_resume(
    resume_id: uuid.UUID,
    session: UserSession = Depends(get_session),
    store: ResumeStore = Depends(get_resume_store),
    analyzer: Analyzer = Depends(get_analyzer),
    writer: ProfileWriter = Depends(get_supabase_admin),
) -> ResumeProfile:
    try:
        # Lido com o token da pessoa: o RLS garante que o currículo é dela.
        resume = await store.get_resume_file(str(resume_id))
        if resume is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Currículo não encontrado.")
        content = await store.download(resume["storage_path"])
    except SupabaseError:
        logger.exception("Falha ao buscar o currículo para análise")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível abrir o currículo agora. Tente de novo."
        ) from None

    try:
        text = extract_text(content, resume["content_type"])
    except UnreadableResumeError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Não conseguimos ler o texto do currículo. Se for um PDF escaneado (imagem), "
            "envie uma versão com texto selecionável.",
        ) from None

    try:
        result = await analyzer.analyze(text)
    except AnalysisUnavailableError:
        logger.exception("IA indisponível")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "A análise está indisponível agora. Tente de novo."
        ) from None
    except AnalysisError:
        logger.exception("IA não devolveu um perfil utilizável")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível analisar o currículo. Tente de novo."
        ) from None

    try:
        await writer.save_profile(
            {
                "resume_id": str(resume_id),
                "user_id": session.user.id,
                **result.profile.model_dump(),
                "model": result.model,
            }
        )
    except SupabaseError:
        logger.exception("Falha ao salvar o perfil")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível salvar a análise. Tente de novo."
        ) from None
    return result.profile
