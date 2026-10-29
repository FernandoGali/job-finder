import json

import httpx
import pytest

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError
from tests.conftest import USER_ID

PROFILE = {
    "target_role": "Analista de Dados",
    "seniority": "junior",
    "skills": ["SQL", "Python"],
    "certifications": [],
    "search_terms": ["Analista de Dados"],
    "summary": "",
    "analyzed_at": "2026-10-28T12:00:00Z",
}

JOBS = [
    {
        "id": "a",
        "title": "Analista de Dados Júnior",
        "company": "Stone",
        "location": "São Paulo",
        "url": "https://job-boards.greenhouse.io/stone/jobs/1",
        "description": "Descrição completa e interna: SQL e Python.",
    },
    {
        "id": "b",
        "title": "Analista de Suporte",
        "company": "VTEX",
        "location": "Remoto",
        "url": "https://job-boards.greenhouse.io/vtex/jobs/2",
        "description": "Atendimento.",
    },
]


class FakeReader:
    def __init__(self) -> None:
        self.fail = False

    async def list_jobs(self):
        if self.fail:
            raise SupabaseError("banco fora")
        return JOBS


@pytest.fixture
def reader(client) -> FakeReader:
    fake = FakeReader()
    client.app.dependency_overrides[get_supabase_admin] = lambda: fake
    return fake


def add_resume(store, profile):
    store.resumes.append(
        {
            "id": f"r{len(store.resumes)}",
            "original_filename": "cv.pdf",
            "content_type": "application/pdf",
            "size_bytes": 10,
            "uploaded_at": "2026-10-28T12:00:00Z",
            "storage_path": f"{USER_ID}/cv.pdf",
            "profile": profile,
        }
    )


def test_lista_as_vagas_que_combinam_sem_a_descricao(client, store, reader):
    add_resume(store, PROFILE)

    response = client.get("/vagas")

    assert response.status_code == 200
    [vaga] = response.json()
    assert vaga["id"] == "a"
    assert vaga["company"] == "Stone"
    assert vaga["url"] == "https://job-boards.greenhouse.io/stone/jobs/1"
    assert "Pede SQL, Python" in vaga["reasons"]
    # Regra 4: a descrição completa não sai da API.
    assert "description" not in vaga
    assert "interna" not in response.text


def test_usa_o_curriculo_analisado_mais_recente(client, store, reader):
    add_resume(store, {**PROFILE, "search_terms": ["Analista de Suporte"], "skills": []})
    add_resume(store, None)  # o mais recente ainda não foi analisado

    [vaga] = client.get("/vagas").json()

    assert vaga["id"] == "b"


def test_sem_curriculo_analisado_pede_a_analise(client, store, reader):
    add_resume(store, None)

    response = client.get("/vagas")

    assert response.status_code == 409
    assert "Analise seu currículo" in response.json()["detail"]


def test_falha_do_banco_vira_502(client, store, reader):
    add_resume(store, PROFILE)
    reader.fail = True

    assert client.get("/vagas").status_code == 502


@pytest.mark.anyio
async def test_admin_lista_as_vagas_em_paginas():
    requests: list[httpx.Request] = []

    def handler(request):
        requests.append(request)
        offset = int(request.url.params["offset"])
        size = 1000 if offset == 0 else 3
        return httpx.Response(200, json=[{"id": str(offset + i)} for i in range(size)])

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    jobs = await SupabaseAdminClient("https://x.supabase.co", "secreta", http).list_jobs()

    assert len(jobs) == 1003
    assert [r.url.params["offset"] for r in requests] == ["0", "1000"]
    assert (
        json.dumps(requests[0].url.params["select"])
        == '"id,title,company,location,url,description"'
    )


DATA_JOBS = [
    {
        "id": str(i),
        "title": "Analista de Dados",
        "company": "Stone",
        "location": "São Paulo",
        "url": f"https://job-boards.greenhouse.io/stone/jobs/{i}",
        "description": "Trecho interno: SQL e Tableau." if i % 2 else "Trecho interno: SQL.",
    }
    for i in range(6)
]


def test_demanda_conta_o_que_as_vagas_de_cada_cargo_pedem(client, store, reader, monkeypatch):
    monkeypatch.setattr(reader, "list_jobs", _returning(DATA_JOBS))
    roles = [
        {"title": "Analista de Dados", "evidence": None, "keywords": ["Tableau"]},
        {"title": "Analista de BI", "evidence": None, "keywords": []},
    ]
    add_resume(store, {**PROFILE, "skills": ["SQL"], "suggested_roles": roles})

    response = client.get("/vagas/demanda")

    assert response.status_code == 200
    [dados, bi] = response.json()
    assert dados["role"] == "Analista de Dados"
    assert dados["jobs"] == 6
    assert dados["items"] == [
        {"name": "SQL", "jobs": 6, "share": 100, "in_resume": True},
        # A palavra-chave do cargo sugerido também conta como citada no currículo.
        {"name": "Tableau", "jobs": 3, "share": 50, "in_resume": True},
    ]
    assert bi == {"role": "Analista de BI", "jobs": 0, "items": []}
    # Regra 4: só contagens, nenhum trecho da vaga.
    assert "interno" not in response.text


def test_demanda_de_analise_antiga_usa_os_termos_de_busca(client, store, reader, monkeypatch):
    monkeypatch.setattr(reader, "list_jobs", _returning(DATA_JOBS))
    add_resume(store, PROFILE)  # sem suggested_roles

    [dados] = client.get("/vagas/demanda").json()

    assert dados["role"] == "Analista de Dados"
    # Python é competência do perfil, mas nenhuma dessas vagas pede.
    assert [item["name"] for item in dados["items"]] == ["SQL", "Tableau"]


def test_demanda_sem_curriculo_analisado_pede_a_analise(client, store, reader):
    add_resume(store, None)

    assert client.get("/vagas/demanda").status_code == 409


def _returning(jobs):
    async def list_jobs():
        return jobs

    return list_jobs
