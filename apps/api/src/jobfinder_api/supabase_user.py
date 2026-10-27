"""Acesso ao Supabase (banco e Storage) em nome do usuário logado.

Toda chamada leva o token da própria pessoa, então as regras de acesso (RLS) do banco
valem aqui também: mesmo um erro neste código não grava na pasta de outra pessoa.
"""

from typing import Any

import httpx

BUCKET = "curriculos"


class SupabaseError(Exception):
    """O Supabase recusou ou não respondeu a uma operação."""


class SupabaseUserClient:
    def __init__(
        self, supabase_url: str, anon_key: str, access_token: str, http: httpx.AsyncClient
    ) -> None:
        self._url = supabase_url.rstrip("/")
        self._headers = {"apikey": anon_key, "Authorization": f"Bearer {access_token}"}
        self._http = http

    async def add_consent(self, user_id: str, purpose: str, version: str) -> str:
        row = await self._insert(
            "consents", {"user_id": user_id, "purpose": purpose, "version": version}
        )
        return row["id"]

    async def upload(self, path: str, content: bytes, content_type: str) -> None:
        await self._request(
            "POST",
            f"/storage/v1/object/{BUCKET}/{path}",
            content=content,
            headers={"Content-Type": content_type, "x-upsert": "false"},
        )

    async def delete_upload(self, path: str) -> None:
        await self._request("DELETE", f"/storage/v1/object/{BUCKET}/{path}")

    async def add_resume(self, resume: dict[str, Any]) -> dict[str, Any]:
        return await self._insert("resumes", resume)

    async def list_resumes(self) -> list[dict[str, Any]]:
        response = await self._request(
            "GET",
            "/rest/v1/resumes",
            params={
                "select": "id,original_filename,content_type,size_bytes,uploaded_at",
                "order": "uploaded_at.desc",
            },
        )
        return response.json()

    async def _insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"/rest/v1/{table}",
            json=row,
            headers={"Prefer": "return=representation"},
        )
        return response.json()[0]

    async def _request(
        self, method: str, path: str, headers: dict[str, str] | None = None, **kwargs: Any
    ) -> httpx.Response:
        try:
            response = await self._http.request(
                method, f"{self._url}{path}", headers={**self._headers, **(headers or {})}, **kwargs
            )
        except httpx.HTTPError as exc:
            raise SupabaseError(f"{method} {path}: sem resposta ({exc})") from exc
        if response.is_error:
            raise SupabaseError(f"{method} {path}: HTTP {response.status_code}")
        return response
