import json
from typing import Any

import httpx
import pytest

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.config import Settings, get_settings
from jobfinder_api.resume_analysis import MODEL, AnalysisError, AnalysisUnavailableError
from jobfinder_api.resume_rewrite import ResumeRewrite, RewriteResult
from jobfinder_api.resumes import PDF
from jobfinder_api.rewrite import get_rewriter
from jobfinder_api.supabase_user import SupabaseAdminClient, SupabaseError
from tests.conftest import USER_ID, pdf_with_text

REWRITE = ResumeRewrite(
    headline="Analista de Dados",
    summary="Resumo.",
    experiences=[],
    education=[],
    skills=["SQL"],
    certifications=[],
    questions=["Quantos relatórios?"],
)

PROFILE = {
    "target_role": "Analista de BI",
    "seniority": "junior",
    "skills": ["SQL", "Excel"],
    "suggested_roles": [
        {"title": "Analista de Dados", "evidence": None, "keywords": ["SQL", "Python"]},
    ],
    "search_terms": ["Analista de Dados"],
}

JOBS = [
    {
        "id": str(i),
        "title": "Analista de Dados",
        "company": "Stone",
        "location": "São Paulo",
        "url": f"https://job-boards.greenhouse.io/stone/jobs/{i}",
        "description": "SQL, Excel e Tableau.",
    }
    for i in range(5)
]


class FakeRewriter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None, list[str]]] = []
        self.error: Exception | None = None

    async def rewrite(self, resume_text, target_role, keywords) -> RewriteResult:
        self.calls.append((resume_text, target_role, keywords))
        if self.error:
            raise self.error
        return RewriteResult(rewrite=REWRITE, model=MODEL)


class FakeBackend:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.fail_save = False
        self.fail_jobs = False

    async def list_jobs(self):
        if self.fail_jobs:
            raise SupabaseError("vagas")
        return JOBS

    async def save_rewrite(self, row):
        if self.fail_save:
            raise SupabaseError("salvar")
        self.rows.append(row)


@pytest.fixture
def rewriter(client) -> FakeRewriter:
    fake = FakeRewriter()
    client.app.dependency_overrides[get_rewriter] = lambda: fake
    return fake


@pytest.fixture
def backend(client) -> FakeBackend:
    fake = FakeBackend()
    client.app.dependency_overrides[get_supabase_admin] = lambda: fake
    return fake


CV = pdf_with_text("Analista de Dados", "SQL")


def add_resume(store, profile=PROFILE, content=CV) -> str:
    path = f"{USER_ID}/cv.pdf"
    store.files[path] = content
    resume_id = "c1111111-1111-1111-1111-111111111111"
    store.resumes.append(
        {"id": resume_id, "storage_path": path, "content_type": PDF, "profile": profile}
    )
    return resume_id


def test_reescreve_com_o_cargo_e_as_palavras_chave_e_guarda(client, store, rewriter, backend):
    resume_id = add_resume(store)

    response = client.post(f"/curriculos/{resume_id}/reescrita")

    assert response.status_code == 200
    assert response.json() == REWRITE.model_dump()
    [(text, target, keywords)] = rewriter.calls
    assert text == "Analista de Dados\nSQL"
    # O primeiro cargo sugerido é o alvo.
    assert target == "Analista de Dados"
    # Palavras-chave do cargo, mais o que as vagas pedem e o currículo já cita (Excel), sem
    # repetir; Tableau as vagas pedem, mas a pessoa não cita: fica de fora.
    assert keywords == ["SQL", "Python", "Excel"]
    assert backend.rows == [
        {
            "resume_id": resume_id,
            "user_id": USER_ID,
            "content": REWRITE.model_dump(),
            "model": MODEL,
        }
    ]


def test_analise_antiga_usa_o_cargo_alvo(client, store, rewriter, backend):
    resume_id = add_resume(store, profile={**PROFILE, "suggested_roles": []})

    client.post(f"/curriculos/{resume_id}/reescrita")

    [(_, target, _)] = rewriter.calls
    assert target == "Analista de BI"


def test_sem_analise_pede_para_analisar_antes(client, store, rewriter, backend):
    resume_id = add_resume(store, profile=None)

    response = client.post(f"/curriculos/{resume_id}/reescrita")

    assert response.status_code == 409
    assert "Analise o currículo" in response.json()["detail"]
    assert rewriter.calls == []


def test_curriculo_de_outra_pessoa_responde_404(client, rewriter, backend):
    response = client.post("/curriculos/99999999-9999-9999-9999-999999999999/reescrita")

    assert response.status_code == 404


def test_pdf_sem_texto_pede_versao_com_texto(client, store, rewriter, backend):
    resume_id = add_resume(store, content=b"%PDF-1.7 quebrado")

    assert client.post(f"/curriculos/{resume_id}/reescrita").status_code == 422
    assert rewriter.calls == []


@pytest.mark.parametrize(
    ("error", "status"),
    [(AnalysisUnavailableError("fora"), 503), (AnalysisError("recusa"), 502)],
)
def test_falhas_da_ia_nao_gravam_nada(client, store, rewriter, backend, error, status):
    resume_id = add_resume(store)
    rewriter.error = error

    assert client.post(f"/curriculos/{resume_id}/reescrita").status_code == status
    assert backend.rows == []


def test_falha_ao_ler_vagas_ou_curriculo(client, store, rewriter, backend):
    resume_id = add_resume(store)
    backend.fail_jobs = True

    assert client.post(f"/curriculos/{resume_id}/reescrita").status_code == 502
    assert rewriter.calls == []


def test_falha_ao_salvar(client, store, rewriter, backend):
    resume_id = add_resume(store)
    backend.fail_save = True

    assert client.post(f"/curriculos/{resume_id}/reescrita").status_code == 502


def test_sem_chave_da_anthropic_fica_indisponivel(client, store, backend):
    resume_id = add_resume(store)
    client.app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)

    response = client.post(f"/curriculos/{resume_id}/reescrita")

    assert response.status_code == 503
    assert "Reescrita indisponível" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_rewriter_cria_o_cliente_com_a_chave():
    settings = Settings(_env_file=None, anthropic_api_key="chave-de-teste")

    async for rewriter in get_rewriter(settings):
        assert rewriter is not None


@pytest.mark.anyio
async def test_admin_grava_a_reescrita_substituindo_a_anterior():
    requests: list[httpx.Request] = []

    def capture(request):
        requests.append(request)
        return httpx.Response(201)

    http = httpx.AsyncClient(transport=httpx.MockTransport(capture))
    await SupabaseAdminClient("https://x.supabase.co", "secreta", http).save_rewrite(
        {"resume_id": "r1", "content": {}}
    )

    [request] = requests
    assert request.url.path == "/rest/v1/resume_rewrites"
    assert request.url.params["on_conflict"] == "resume_id"
    assert request.headers["Prefer"] == "resolution=merge-duplicates,return=minimal"
    assert json.loads(request.content) == {"resume_id": "r1", "content": {}}
