"""Exclusão da conta (LGPD): apaga os arquivos, a conta e, em cascata, os registros."""

import logging
from collections.abc import AsyncIterator
from typing import Protocol

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from jobfinder_api.auth import UserSession, get_session
from jobfinder_api.config import Settings, get_settings
from jobfinder_api.resumes import ResumeStore, get_resume_store
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError

logger = logging.getLogger(__name__)


class AccountAdmin(Protocol):
    async def delete_user(self, user_id: str) -> None: ...


async def get_account_admin(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[AccountAdmin]:
    if not (settings.supabase_url and settings.supabase_service_role_key):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "Exclusão de conta indisponível no momento."
        )
    async with httpx.AsyncClient(timeout=30) as http:
        yield SupabaseAdminClient(settings.supabase_url, settings.supabase_service_role_key, http)


router = APIRouter()


@router.delete("/conta", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    session: UserSession = Depends(get_session),
    store: ResumeStore = Depends(get_resume_store),
    admin: AccountAdmin = Depends(get_account_admin),
) -> None:
    """Primeiro os arquivos (com o token da pessoa), depois a conta.

    Apagar a conta remove consents e resumes pelo "on delete cascade". Se algo falhar no
    meio, a pessoa pode tentar de novo: arquivos já apagados são ignorados.
    """
    user_id = session.user.id
    try:
        await store.delete_files(await store.list_files(user_id))
        await admin.delete_user(user_id)
    except SupabaseError:
        logger.exception("Falha ao excluir conta")
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "Não foi possível excluir sua conta agora. Tente de novo."
        ) from None
