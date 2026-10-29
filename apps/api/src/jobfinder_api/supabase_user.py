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
# Vagas gravadas por pedido; a descrição completa deixa cada vaga com alguns KB.
JOBS_BATCH = 200
# O Supabase devolve no máximo 1.000 linhas por pedido.
JOBS_PAGE = 1000


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

    async def upsert_jobs(self, rows: list[dict[str, Any]]) -> None:
        """Grava vagas novas e atualiza as que já existem (mesma fonte e mesmo id)."""
        for start in range(0, len(rows), JOBS_BATCH):
            await self._request(
                "POST",
                "/rest/v1/jobs",
                params={"on_conflict": "source,external_id"},
                json=rows[start : start + JOBS_BATCH],
                headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
            )

    async def list_jobs(self) -> list[dict[str, Any]]:
        """Todas as vagas, com a descrição (para comparar com o perfil; não sai da API)."""
        rows: list[dict[str, Any]] = []
        while True:
            response = await self._request(
                "GET",
                "/rest/v1/jobs",
                params={
                    "select": "id,title,company,location,url,description",
                    "order": "id",
                    "limit": str(JOBS_PAGE),
                    "offset": str(len(rows)),
                },
            )
            page = response.json()
            rows.extend(page)
            if len(page) < JOBS_PAGE:
                return rows

    async def delete_stale_jobs(self, source: str, board: str, before: str) -> None:
        """Apaga as vagas do quadro que não vieram na coleta atual (já fecharam)."""
        await self._request(
            "DELETE",
            "/rest/v1/jobs",
            params={"source": f"eq.{source}", "board": f"eq.{board}", "fetched_at": f"lt.{before}"},
        )

    async def save_rewrite(self, row: dict[str, Any]) -> None:
        """Grava (ou substitui) a reescrita de um currículo. Só a API grava reescritas."""
        await self._request(
            "POST",
            "/rest/v1/resume_rewrites",
            params={"on_conflict": "resume_id"},
            json=row,
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )

    async def save_profile(self, row: dict[str, Any]) -> None:
        """Grava (ou substitui) o perfil de um currículo. Só a API grava perfis."""
        await self._request(
            "POST",
            "/rest/v1/resume_profiles",
            params={"on_conflict": "resume_id"},
            json=row,
            headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
        )


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
                "select": (
                    "id,original_filename,content_type,size_bytes,uploaded_at,"
                    "profile:resume_profiles(target_role,seniority,skills,certifications,suggested_roles,search_terms,summary,analyzed_at),"
                    "rewrite:resume_rewrites(content,created_at)"
                ),
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

    async def get_resume_file(self, resume_id: str) -> dict[str, str] | None:
        """Caminho e tipo do arquivo, ou None se o currículo não existe (ou não é seu)."""
        response = await self._request(
            "GET",
            "/rest/v1/resumes",
            params={"id": f"eq.{resume_id}", "select": "storage_path,content_type"},
        )
        rows = response.json()
        return rows[0] if rows else None

    async def download(self, path: str) -> bytes:
        response = await self._request("GET", f"/storage/v1/object/authenticated/{BUCKET}/{path}")
        return response.content

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
