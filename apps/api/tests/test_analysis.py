from typing import Any

import pytest
from fastapi import HTTPException

from jobfinder_api.admin import get_supabase_admin
from jobfinder_api.analysis import get_analyzer
from jobfinder_api.config import Settings
from jobfinder_api.resume_analysis import (
    MODEL,
    AnalysisError,
    AnalysisResult,
    AnalysisUnavailableError,
    ResumeAnalyzer,
    ResumeProfile,
)
from jobfinder_api.resumes import PDF
from jobfinder_api.supabase_user import SupabaseError
from tests.conftest import USER_ID, pdf_with_text

PROFILE = ResumeProfile(
    target_role="Analista de Dados", seniority="pleno", skills=["Python", "SQL"], summary="Resumo."
)


class FakeAnalyzer:
    def __init__(self, error: Exception | None = None) -> None:
        self.texts: list[str] = []
        self.error = error

    async def analyze(self, resume_text: str) -> AnalysisResult:
        self.texts.append(resume_text)
        if self.error:
            raise self.error
        return AnalysisResult(profile=PROFILE, model=MODEL)


class FakeWriter:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.fail = False

    async def save_profile(self, row: dict[str, Any]) -> None:
        if self.fail:
            raise SupabaseError("salvar")
        self.rows.append(row)


@pytest.fixture
def analyzer(client) -> FakeAnalyzer:
    fake = FakeAnalyzer()
    client.app.dependency_overrides[get_analyzer] = lambda: fake
    return fake


@pytest.fixture
def writer(client) -> FakeWriter:
    fake = FakeWriter()
    client.app.dependency_overrides[get_supabase_admin] = lambda: fake
    return fake


def add_resume(store, content: bytes = pdf_with_text("Analista de Dados", "Python e SQL")) -> str:
    path = f"{USER_ID}/cv.pdf"
    store.files[path] = content
    resume_id = "c1111111-1111-1111-1111-111111111111"
    store.resumes.append(
        {"id": resume_id, "storage_path": path, "content_type": PDF, "user_id": USER_ID}
    )
    return resume_id


def test_analisa_o_curriculo_e_guarda_o_perfil(client, store, analyzer, writer):
    resume_id = add_resume(store)

    response = client.post(f"/curriculos/{resume_id}/analise")

    assert response.status_code == 200
    assert response.json() == PROFILE.model_dump()
    assert analyzer.texts == ["Analista de Dados\nPython e SQL"]
    assert writer.rows == [
        {
            "resume_id": resume_id,
            "user_id": USER_ID,
            **PROFILE.model_dump(),
            "model": MODEL,
        }
    ]


def test_curriculo_inexistente_ou_de_outra_pessoa_responde_404(client, analyzer, writer):
    response = client.post("/curriculos/99999999-9999-9999-9999-999999999999/analise")

    assert response.status_code == 404
    assert analyzer.texts == []


def test_pdf_sem_texto_pede_versao_com_texto_selecionavel(client, store, analyzer, writer):
    resume_id = add_resume(store, content=b"%PDF-1.7 quebrado")

    response = client.post(f"/curriculos/{resume_id}/analise")

    assert response.status_code == 422
    assert "texto selecionável" in response.json()["detail"]
    assert analyzer.texts == []


@pytest.mark.parametrize(
    ("error", "status"),
    [(AnalysisUnavailableError("fora"), 503), (AnalysisError("recusa"), 502)],
)
def test_falhas_da_ia_nao_gravam_nada(client, store, analyzer, writer, error, status):
    resume_id = add_resume(store)
    analyzer.error = error

    assert client.post(f"/curriculos/{resume_id}/analise").status_code == status
    assert writer.rows == []


def test_falha_ao_buscar_o_curriculo(client, store, analyzer, writer):
    resume_id = add_resume(store)
    store.fail_on.add("get_file")

    assert client.post(f"/curriculos/{resume_id}/analise").status_code == 502


def test_falha_ao_salvar_o_perfil(client, store, analyzer, writer):
    resume_id = add_resume(store)
    writer.fail = True

    assert client.post(f"/curriculos/{resume_id}/analise").status_code == 502


@pytest.mark.anyio
async def test_analise_indisponivel_sem_chave_da_anthropic():
    generator = get_analyzer(Settings(_env_file=None, anthropic_api_key=""))

    with pytest.raises(HTTPException) as exc:
        await anext(generator)

    assert exc.value.status_code == 503


@pytest.mark.anyio
async def test_analisador_usa_a_chave_configurada():
    generator = get_analyzer(Settings(_env_file=None, anthropic_api_key="sk-ant-teste"))

    analyzer = await anext(generator)

    assert isinstance(analyzer, ResumeAnalyzer)
    assert analyzer._client.api_key == "sk-ant-teste"
    await generator.aclose()
