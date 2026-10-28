"""Coleta de vagas: lê as fontes e guarda no banco.

Por enquanto roda à mão, da pasta apps/api:  python -m jobfinder_api.job_sync
"""

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
from pydantic import BaseModel

from jobfinder_api.config import get_settings
from jobfinder_api.job_sources import (
    GREENHOUSE_BOARDS,
    JobPosting,
    JobSourceError,
    fetch_greenhouse,
)
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError


class JobStore(Protocol):
    async def upsert_jobs(self, rows: list[dict[str, Any]]) -> None: ...
    async def delete_stale_jobs(self, source: str, board: str, before: str) -> None: ...


class SyncReport(BaseModel):
    saved: dict[str, int] = {}
    failed: dict[str, str] = {}


async def sync_greenhouse(
    fetch: Callable[[str], Awaitable[list[JobPosting]]],
    store: JobStore,
    boards: Iterable[str],
    now: datetime,
) -> SyncReport:
    """Cada quadro é independente: se um falhar, os outros seguem e as vagas dele ficam como
    estavam (nada é apagado por causa de uma falha de rede)."""
    report = SyncReport()
    stamp = now.isoformat()
    for board in boards:
        try:
            jobs = await fetch(board)
            rows = [{**job.model_dump(mode="json"), "fetched_at": stamp} for job in jobs]
            if rows:
                await store.upsert_jobs(rows)
            await store.delete_stale_jobs("greenhouse", board, stamp)
        except (JobSourceError, SupabaseError) as exc:
            report.failed[board] = str(exc)
            continue
        report.saved[board] = len(rows)
    return report


async def main(transport: httpx.AsyncBaseTransport | None = None) -> int:
    settings = get_settings()
    if not (settings.supabase_url and settings.supabase_service_role_key):
        print("Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env antes de coletar.")
        return 2
    async with httpx.AsyncClient(timeout=60, transport=transport) as http:
        store = SupabaseAdminClient(settings.supabase_url, settings.supabase_service_role_key, http)
        report = await sync_greenhouse(
            lambda board: fetch_greenhouse(http, board), store, GREENHOUSE_BOARDS, datetime.now(UTC)
        )
    for board, count in report.saved.items():
        print(f"ok    {board}: {count} vagas")
    for board, error in report.failed.items():
        print(f"falha {board}: {error}")
    return 1 if report.failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(asyncio.run(main()))
