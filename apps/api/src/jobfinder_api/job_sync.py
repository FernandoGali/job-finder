"""Coleta de vagas: lê as fontes e guarda no banco.

Roda todo dia pelo GitHub Actions (.github/workflows/coleta-vagas.yml), ou à mão, da pasta
apps/api:  python -m jobfinder_api.job_sync
"""

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
from pydantic import BaseModel

from jobfinder_api import job_sources
from jobfinder_api.config import get_settings
from jobfinder_api.job_sources import (
    GREENHOUSE_BOARDS,
    LEVER_BOARDS,
    JobPosting,
    JobSourceError,
    fetch_greenhouse,
    fetch_lever,
)
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError


class JobStore(Protocol):
    async def upsert_jobs(self, rows: list[dict[str, Any]]) -> None: ...
    async def delete_stale_jobs(self, source: str, board: str, before: str) -> None: ...


class SyncReport(BaseModel):
    saved: dict[str, int] = {}
    failed: dict[str, str] = {}


async def sync_boards(
    fetch: Callable[[str, str], Awaitable[list[JobPosting]]],
    store: JobStore,
    boards: Iterable[tuple[str, str]],
    now: datetime,
) -> SyncReport:
    """Cada quadro (fonte, empresa) é independente: se um falhar, os outros seguem e as vagas
    dele ficam como estavam (nada é apagado por causa de uma falha de rede)."""
    report = SyncReport()
    stamp = now.isoformat()
    for source, board in boards:
        key = f"{source}/{board}"
        try:
            jobs = await fetch(source, board)
            rows = [{**job.model_dump(mode="json"), "fetched_at": stamp} for job in jobs]
            if rows:
                await store.upsert_jobs(rows)
            await store.delete_stale_jobs(source, board, stamp)
        except (JobSourceError, SupabaseError) as exc:
            report.failed[key] = str(exc)
            continue
        report.saved[key] = len(rows)
    return report


def all_boards() -> list[tuple[str, str]]:
    return [("greenhouse", board) for board in GREENHOUSE_BOARDS] + [
        ("lever", board) for board in LEVER_BOARDS
    ]


async def main(transport: httpx.AsyncBaseTransport | None = None) -> int:
    settings = get_settings()
    if not (settings.supabase_url and settings.supabase_service_role_key):
        print("Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY no .env antes de coletar.")
        return 2
    async with httpx.AsyncClient(timeout=60, transport=transport) as http:
        store = SupabaseAdminClient(settings.supabase_url, settings.supabase_service_role_key, http)

        async def fetch(source: str, board: str) -> list[JobPosting]:
            if source == "lever":
                await asyncio.sleep(job_sources.LEVER_DELAY)
                return await fetch_lever(http, board)
            return await fetch_greenhouse(http, board)

        report = await sync_boards(fetch, store, all_boards(), datetime.now(UTC))
    for board, count in report.saved.items():
        print(f"ok    {board}: {count} vagas")
    for board, error in report.failed.items():
        print(f"falha {board}: {error}")
    return 1 if report.failed else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(asyncio.run(main()))
