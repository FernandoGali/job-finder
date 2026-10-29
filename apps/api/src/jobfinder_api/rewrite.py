"""Rota que reescreve o currículo para ATS e guarda o resultado."""

import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any, Protocol

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.auth import UserSession, get_session
from jobfinder_api.config import Settings, get_settings
from jobfinder_api.job_demand import market_demand, resume_terms
from jobfinder_api.job_matching import JobForMatching
from jobfinder_api.resume_analysis import AnalysisError, AnalysisUnavailableError
from jobfinder_api.resume_rewrite import ResumeRewrite, ResumeRewriter, RewriteResult
from jobfinder_api.resume_text import UnreadableResumeError, extract_text
from jobfinder_api.resumes import ResumeStore, get_resume_store
from jobfinder_api.supabase_user import SupabaseError

logger = logging.getLogger(__name__)


class Rewriter(Protocol):
    async def rewrite(
        self, resume_text: str, target_role: str | None, keywords: list[str]
    ) -> RewriteResult: ...


class RewriteBackend(Protocol):
    async def list_jobs(self) -> list[dict[str, Any]]: ...
    async def save_rewrite(self, row: dict[str, Any]) -> None: ...


async def get_rewriter(settings: Settings = Depends(get_settings)) -> AsyncIterator[Rewriter]:
    if not settings.anthropic_api_key:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Reescrita indisponível no momento."
        )
    async with anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key) as client:
        yield ResumeRewriter(client)


def rewrite_keywords(profile: dict[str, Any], jobs: list[JobForMatching]) -> list[str]:
    """Palavras-chave que a pessoa de fato domina: as dos cargos sugeridos (conferidas no
    currículo na análise) e o que as vagas do cargo pedem e o currículo já cita."""
    roles = profile.get("suggested_roles") or []
    titles = [role["title"] for role in roles] or profile.get("search_terms") or []
    demand = market_demand(titles, jobs, resume_terms(profile), profile.get("seniority"))
    keywords = [keyword for role in roles for keyword in role.get("keywords", [])]
    keywords += [item.name for role in demand for item in role.items if item.in_resume]
    return list(dict.fromkeys(keywords))


router = APIRouter()


@router.post("/curriculos/{resume_id}/reescrita", response_model=ResumeRewrite)
async def rewrite_resume(
    resume_id: uuid.UUID,
    session: UserSession = Depends(get_session),
    store: ResumeStore = Depends(get_resume_store),
    rewriter: Rewriter = Depends(get_rewriter),
    backend: RewriteBackend = Depends(get_supabase_admin),
) -> ResumeRewrite:
    try:
        # Lido com o token da pessoa: o RLS garante que o currículo é dela.
        resume = await store.get_resume_file(str(resume_id))
        if resume is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Currículo não encontrado.")
        resumes = await store.list_resumes()
        profile = next(
            (r.get("profile") for r in resumes if r["id"] == str(resume_id) and r.get("profile")),
            None,
        )
        if profile is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Analise o currículo antes de reescrever."
            )
        content = await store.download(resume["storage_path"])
        jobs = [JobForMatching(**job) for job in await backend.list_jobs()]
    except SupabaseError:
        logger.exception("Falha ao preparar a reescrita")
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

    roles = profile.get("suggested_roles") or []
    target_role = roles[0]["title"] if roles else profile.get("target_role")
    try:
        result = await rewriter.rewrite(text, target_role, rewrite_keywords(profile, jobs))
    except AnalysisUnavailableError:
        logger.exception("IA indisponível")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "A reescrita está indisponível agora. Tente de novo.",
        ) from None
    except AnalysisError:
        logger.exception("IA não devolveu uma reescrita utilizável")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível reescrever o currículo. Tente de novo."
        ) from None

    try:
        await backend.save_rewrite(
            {
                "resume_id": str(resume_id),
                "user_id": session.user.id,
                "content": result.rewrite.model_dump(),
                "model": result.model,
            }
        )
    except SupabaseError:
        logger.exception("Falha ao salvar a reescrita")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível salvar a reescrita. Tente de novo."
        ) from None
    return result.rewrite
