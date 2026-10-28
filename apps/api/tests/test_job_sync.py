import json
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from jobfinder_api import job_sync
from jobfinder_api.config import Settings
from jobfinder_api.job_sources import JobPosting, JobSourceError
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


def posting(board: str, external_id: str) -> JobPosting:
    return JobPosting(
        source="greenhouse",
        board=board,
        external_id=external_id,
        company=board.title(),
        title="Analista de Dados",
        location="Brasil",
        description="SQL e Python",
        url=f"https://job-boards.greenhouse.io/{board}/jobs/{external_id}",
        published_at=None,
        updated_at=None,
    )


class FakeStore:
    def __init__(self) -> None:
        self.upserts: list[list[dict[str, Any]]] = []
        self.deletes: list[tuple[str, str, str]] = []
        self.fail = False

    async def upsert_jobs(self, rows):
        if self.fail:
            raise SupabaseError("banco fora")
        self.upserts.append(rows)

    async def delete_stale_jobs(self, source, board, before):
        self.deletes.append((source, board, before))


async def test_grava_as_vagas_e_apaga_as_que_fecharam():
    store = FakeStore()

    async def fetch(board):
        return [posting(board, "1"), posting(board, "2")]

    report = await job_sync.sync_greenhouse(fetch, store, ["stone"], NOW)

    assert report.saved == {"stone": 2}
    assert report.failed == {}
    [rows] = store.upserts
    assert [row["external_id"] for row in rows] == ["1", "2"]
    assert rows[0]["fetched_at"] == NOW.isoformat()
    # Tudo que não veio nesta coleta (fetched_at mais antigo) é apagado.
    assert store.deletes == [("greenhouse", "stone", NOW.isoformat())]


async def test_quadro_sem_vagas_apaga_as_antigas_sem_gravar_nada():
    store = FakeStore()

    async def fetch(board):
        return []

    report = await job_sync.sync_greenhouse(fetch, store, ["nubank"], NOW)

    assert report.saved == {"nubank": 0}
    assert store.upserts == []
    assert store.deletes == [("greenhouse", "nubank", NOW.isoformat())]


async def test_falha_numa_fonte_nao_apaga_nada_dela_e_nao_para_as_outras():
    store = FakeStore()

    async def fetch(board):
        if board == "stone":
            raise JobSourceError("greenhouse/stone: sem rede")
        return [posting(board, "1")]

    report = await job_sync.sync_greenhouse(fetch, store, ["stone", "vtex"], NOW)

    assert report.failed == {"stone": "greenhouse/stone: sem rede"}
    assert report.saved == {"vtex": 1}
    assert [delete[1] for delete in store.deletes] == ["vtex"]


async def test_falha_ao_gravar_entra_no_relatorio_e_nao_apaga():
    store = FakeStore()
    store.fail = True

    async def fetch(board):
        return [posting(board, "1")]

    report = await job_sync.sync_greenhouse(fetch, store, ["vtex"], NOW)

    assert "vtex" in report.failed
    assert store.deletes == []


async def test_main_coleta_de_ponta_a_ponta(monkeypatch, capsys):
    monkeypatch.setattr(
        job_sync,
        "get_settings",
        lambda: Settings(
            _env_file=None,
            supabase_url="https://x.supabase.co",
            supabase_service_role_key="secreta",
        ),
    )
    monkeypatch.setattr(job_sync, "GREENHOUSE_BOARDS", {"vtex": "VTEX", "fora": "Fora"})
    saved: list[Any] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "boards-api.greenhouse.io":
            if "/fora/" in request.url.path:
                return httpx.Response(503)
            job = {"id": 7, "title": "Analista", "absolute_url": "https://a.io/7"}
            return httpx.Response(200, json={"jobs": [job]})
        if request.method == "POST":
            saved.extend(json.loads(request.content))
        return httpx.Response(201)

    code = await job_sync.main(transport=httpx.MockTransport(handler))

    assert code == 1  # um quadro falhou
    assert [row["external_id"] for row in saved] == ["7"]
    output = capsys.readouterr().out
    assert "ok    vtex: 1 vagas" in output
    assert "falha fora" in output


async def test_main_sem_configuracao_avisa_e_nao_coleta(monkeypatch, capsys):
    monkeypatch.setattr(job_sync, "get_settings", lambda: Settings(_env_file=None))

    assert await job_sync.main() == 2
    assert "SUPABASE_SERVICE_ROLE_KEY" in capsys.readouterr().out


def _admin(requests: list[httpx.Request], status: int) -> SupabaseAdminClient:
    def capture(request):
        requests.append(request)
        return httpx.Response(status)

    http = httpx.AsyncClient(transport=httpx.MockTransport(capture))
    return SupabaseAdminClient("https://x.supabase.co", "secreta", http)


async def test_admin_grava_vagas_em_lotes():
    requests: list[httpx.Request] = []

    await _admin(requests, 201).upsert_jobs([{"external_id": str(i)} for i in range(450)])

    assert [len(json.loads(r.content)) for r in requests] == [200, 200, 50]
    assert requests[0].url.params["on_conflict"] == "source,external_id"
    assert requests[0].headers["Prefer"] == "resolution=merge-duplicates,return=minimal"


async def test_admin_apaga_vagas_que_nao_vieram_na_coleta():
    requests: list[httpx.Request] = []

    await _admin(requests, 204).delete_stale_jobs("greenhouse", "stone", "2026-10-28T12:00:00")

    [request] = requests
    assert request.method == "DELETE"
    assert dict(request.url.params) == {
        "source": "eq.greenhouse",
        "board": "eq.stone",
        "fetched_at": "lt.2026-10-28T12:00:00",
    }
