"""Vagas recomendadas: as vagas coletadas, ordenadas pelo perfil da pessoa logada."""

import logging
from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, status

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.job_matching import JobForMatching, JobMatch, ProfileForMatching, rank_jobs
from jobfinder_api.resumes import ResumeStore, get_resume_store
from jobfinder_api.supabase_user import SupabaseError

logger = logging.getLogger(__name__)


class JobReader(Protocol):
    async def list_jobs(self) -> list[dict[str, Any]]: ...


router = APIRouter()


@router.get("/vagas", response_model=list[JobMatch])
async def recommended_jobs(
    store: ResumeStore = Depends(get_resume_store),
    reader: JobReader = Depends(get_supabase_admin),
) -> list[JobMatch]:
    """Usa o perfil do currículo analisado mais recente. A descrição completa da vaga só é usada
    aqui dentro: a resposta tem título, empresa, local, link e o motivo de combinar (regra 4)."""
    try:
        resumes = await store.list_resumes()
        profile = next((r["profile"] for r in resumes if r.get("profile")), None)
        if profile is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Analise seu currículo para ver as vagas que combinam."
            )
        jobs = await reader.list_jobs()
    except SupabaseError:
        logger.exception("Falha ao montar as vagas recomendadas")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível carregar as vagas agora. Tente de novo."
        ) from None

    return rank_jobs(
        ProfileForMatching(
            search_terms=profile.get("search_terms") or [],
            skills=profile.get("skills") or [],
            seniority=profile.get("seniority"),
        ),
        [JobForMatching(**job) for job in jobs],
    )
