"""Vagas recomendadas: as vagas coletadas, ordenadas pelo perfil da pessoa logada. E o que as
vagas pedem para cada cargo sugerido."""

import logging
from typing import Any, Protocol

from fastapi import APIRouter, Depends, HTTPException, status

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.job_demand import RoleDemand, market_demand
from jobfinder_api.job_matching import JobForMatching, JobMatch, ProfileForMatching, rank_jobs
from jobfinder_api.resumes import ResumeStore, get_resume_store
from jobfinder_api.supabase_user import SupabaseError

logger = logging.getLogger(__name__)


class JobReader(Protocol):
    async def list_jobs(self) -> list[dict[str, Any]]: ...


router = APIRouter()


async def _profile_and_jobs(
    store: ResumeStore, reader: JobReader
) -> tuple[dict[str, Any], list[JobForMatching]]:
    """Perfil do currículo analisado mais recente e todas as vagas coletadas."""
    try:
        resumes = await store.list_resumes()
        profile = next((r["profile"] for r in resumes if r.get("profile")), None)
        if profile is None:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Analise seu currículo para ver as vagas que combinam."
            )
        jobs = await reader.list_jobs()
    except SupabaseError:
        logger.exception("Falha ao carregar perfil e vagas")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível carregar as vagas agora. Tente de novo."
        ) from None
    return profile, [JobForMatching(**job) for job in jobs]


@router.get("/vagas", response_model=list[JobMatch])
async def recommended_jobs(
    store: ResumeStore = Depends(get_resume_store),
    reader: JobReader = Depends(get_supabase_admin),
) -> list[JobMatch]:
    """A descrição completa da vaga só é usada aqui dentro: a resposta tem título, empresa,
    local, link e o motivo de combinar (regra 4)."""
    profile, jobs = await _profile_and_jobs(store, reader)
    return rank_jobs(
        ProfileForMatching(
            search_terms=profile.get("search_terms") or [],
            skills=profile.get("skills") or [],
            seniority=profile.get("seniority"),
        ),
        jobs,
    )


@router.get("/vagas/demanda", response_model=list[RoleDemand])
async def job_demand(
    store: ResumeStore = Depends(get_resume_store),
    reader: JobReader = Depends(get_supabase_admin),
) -> list[RoleDemand]:
    """Para cada cargo sugerido, os itens mais pedidos nas vagas coletadas e se o currículo os
    cita. Só contagens: nenhum trecho de vaga sai da API (regra 4)."""
    profile, jobs = await _profile_and_jobs(store, reader)
    roles = profile.get("suggested_roles") or []
    titles = [role["title"] for role in roles] or profile.get("search_terms") or []
    # Competências, não cursos: "Fundamentos do Python 1" não quer dizer que a pessoa usa Python.
    resume_terms = [
        *(profile.get("skills") or []),
        *(keyword for role in roles for keyword in role.get("keywords", [])),
    ]
    return market_demand(titles, jobs, resume_terms)
