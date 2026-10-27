"""Conexão com o Supabase usando a chave secreta (só no backend, só para o necessário)."""

from collections.abc import AsyncIterator

import httpx
from fastapi import Depends, HTTPException, status

from jobfinder_api.config import Settings, get_settings
from jobfinder_api.supabase_user import SupabaseAdminClient


async def get_supabase_admin(
    settings: Settings = Depends(get_settings),
) -> AsyncIterator[SupabaseAdminClient]:
    if not (settings.supabase_url and settings.supabase_service_role_key):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Serviço indisponível no momento.")
    async with httpx.AsyncClient(timeout=30) as http:
        yield SupabaseAdminClient(settings.supabase_url, settings.supabase_service_role_key, http)
