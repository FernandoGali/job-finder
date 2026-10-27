"""Exclusão da conta (LGPD): apaga os arquivos, a conta e, em cascata, os registros."""

import logging
from typing import Protocol

from fastapi import APIRouter, Depends, HTTPException, status

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.auth import UserSession, get_session
from jobfinder_api.resumes import ResumeStore, get_resume_store
from jobfinder_api.supabase_user import SupabaseError

logger = logging.getLogger(__name__)


class AccountAdmin(Protocol):
    async def delete_user(self, user_id: str) -> None: ...


router = APIRouter()


@router.delete("/conta", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    session: UserSession = Depends(get_session),
    store: ResumeStore = Depends(get_resume_store),
    admin: AccountAdmin = Depends(get_supabase_admin),
) -> None:
    """Primeiro os arquivos (com o token da pessoa), depois a conta.

    Apagar a conta remove consents, resumes e resume_profiles pelo "on delete cascade".
    Se algo falhar no meio, a pessoa pode tentar de novo: arquivos já apagados são ignorados.
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
