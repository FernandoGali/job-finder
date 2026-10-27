"""Acesso ao Supabase (banco, Storage e Auth).

SupabaseUserClient age em nome do usuário logado: toda chamada leva o token da própria
pessoa, então as regras de acesso (RLS) do banco valem aqui também e mesmo um erro neste
código não mexe na pasta de outra pessoa.

SupabaseAdminClient usa a chave secreta e serve só para o que o usuário não pode fazer
sozinho (hoje: apagar a própria conta).
"""

from typing import Any

import httpx

BUCKET = "curriculos"
# Limite de itens por listagem no Storage; um usuário tem poucos currículos.
LIST_LIMIT = 1000


class SupabaseError(Exception):
    """O Supabase recusou ou não respondeu a uma operação."""


class _SupabaseHttp:
    def __init__(self, supabase_url: str, headers: dict[str, str], http: httpx.AsyncClient):
        self._url = supabase_url.rstrip("/")
        self._headers = headers
        self._http = http

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


class SupabaseAdminClient(_SupabaseHttp):
    def __init__(self, supabase_url: str, service_key: str, http: httpx.AsyncClient) -> None:
        super().__init__(
            supabase_url, {"apikey": service_key, "Authorization": f"Bearer {service_key}"}, http
        )

    async def delete_user(self, user_id: str) -> None:
        await self._request("DELETE", f"/auth/v1/admin/users/{user_id}")


class SupabaseUserClient(_SupabaseHttp):
    def __init__(
        self, supabase_url: str, anon_key: str, access_token: str, http: httpx.AsyncClient
    ) -> None:
        super().__init__(
            supabase_url, {"apikey": anon_key, "Authorization": f"Bearer {access_token}"}, http
        )

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

    async def get_resume_path(self, resume_id: str) -> str | None:
        """Caminho do arquivo no Storage, ou None se o currículo não existe (ou não é seu)."""
        response = await self._request(
            "GET",
            "/rest/v1/resumes",
            params={"id": f"eq.{resume_id}", "select": "storage_path"},
        )
        rows = response.json()
        return rows[0]["storage_path"] if rows else None

    async def delete_resume(self, resume_id: str) -> None:
        await self._request("DELETE", "/rest/v1/resumes", params={"id": f"eq.{resume_id}"})

    async def list_files(self, user_id: str) -> list[str]:
        """Todos os arquivos da pasta da pessoa, inclusive algum sem registro."""
        response = await self._request(
            "POST",
            f"/storage/v1/object/list/{BUCKET}",
            json={"prefix": user_id, "limit": LIST_LIMIT},
        )
        # Itens sem id são subpastas, não arquivos.
        return [f"{user_id}/{item['name']}" for item in response.json() if item.get("id")]

    async def delete_files(self, paths: list[str]) -> None:
        """Apaga vários arquivos. Caminhos que já não existem são ignorados pelo Storage."""
        if paths:
            await self._request("DELETE", f"/storage/v1/object/{BUCKET}", json={"prefixes": paths})

    async def _insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"/rest/v1/{table}",
            json=row,
            headers={"Prefer": "return=representation"},
        )
        return response.json()[0]
