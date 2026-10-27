import json
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest

from jobfinder_api.resume_analysis import (
    MODEL,
    OUTPUT_SCHEMA,
    AnalysisError,
    AnalysisUnavailableError,
    ResumeAnalyzer,
)

pytestmark = pytest.mark.anyio

RESUME = """Maria Silva
Objetivo: Analista de Dados Pleno
Experiência: 4 anos como Analista de BI na Empresa X
Ferramentas: Python, SQL, Power BI, C++
Cursos: Fundamentos do Python 1 (Cisco), Linux Unhatched
"""


def answer(**overrides: Any) -> dict[str, Any]:
    return {
        "target_role": "Analista de Dados",
        "target_role_evidence": "Objetivo: Analista de Dados Pleno",
        "seniority": "pleno",
        "seniority_reason": "4 anos de experiência.",
        "skills": ["Python", "SQL", "Power BI", "C++"],
        "certifications": ["Fundamentos do Python 1", "Linux Unhatched"],
        "summary": "Analista de BI com 4 anos de experiência.",
        **overrides,
    }


class FakeClaude:
    """Faz o papel do AsyncAnthropic: guarda o pedido e devolve uma resposta pronta."""

    def __init__(self, text: str | None = None, stop_reason: str = "end_turn", error=None):
        self.requests: list[dict[str, Any]] = []
        self._text = text
        self._stop_reason = stop_reason
        self._error = error
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs: Any) -> SimpleNamespace:
        self.requests.append(kwargs)
        if self._error:
            raise self._error
        content = [] if self._text is None else [SimpleNamespace(type="text", text=self._text)]
        return SimpleNamespace(content=content, stop_reason=self._stop_reason, model=MODEL)


async def analyze(fake: FakeClaude, resume: str = RESUME):
    return await ResumeAnalyzer(fake).analyze(resume)


async def test_extrai_o_perfil_do_curriculo():
    fake = FakeClaude(json.dumps(answer()))

    result = await analyze(fake)

    assert result.model == MODEL
    assert result.profile.model_dump() == {
        "target_role": "Analista de Dados",
        "seniority": "pleno",
        "skills": ["Python", "SQL", "Power BI", "C++"],
        "certifications": ["Fundamentos do Python 1", "Linux Unhatched"],
        "summary": "Analista de BI com 4 anos de experiência.",
    }


async def test_pedido_usa_o_modelo_o_formato_e_o_fallback_combinados():
    fake = FakeClaude(json.dumps(answer()))

    await analyze(fake)

    [request] = fake.requests
    assert request["model"] == "claude-opus-5-5"
    assert request["fallbacks"] == "default"
    assert request["betas"] == ["server-side-fallback-2026-07-01"]
    assert request["output_config"] == {
        "effort": "medium",
        "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
    }
    # O currículo vai marcado como dado, e as instruções exigem não inventar nada.
    assert request["messages"] == [
        {"role": "user", "content": f"<curriculo>\n{RESUME}\n</curriculo>"}
    ]
    assert "Não invente" in request["system"]
    # Nome de curso não é competência (os cursos citados no currículo não entram na lista).
    assert "Nome de curso, treinamento ou certificação não é competência" in request["system"]


async def test_descarta_competencias_que_nao_estao_no_curriculo():
    fake = FakeClaude(json.dumps(answer(skills=["Python", "Kubernetes", "python", " SQL "])))

    result = await analyze(fake)

    # Kubernetes não aparece no texto; "python" repetido e espaços sobrando também saem.
    assert result.profile.skills == ["Python", "SQL"]


async def test_competencia_curta_precisa_aparecer_como_palavra_inteira():
    fake = FakeClaude(json.dumps(answer(skills=["R", "C", "C++"])))

    result = await analyze(fake)

    # "R" e "C" só aparecem dentro de outras palavras; "C++" aparece de verdade.
    assert result.profile.skills == ["C++"]


async def test_cargo_sem_evidencia_no_curriculo_fica_vazio():
    fake = FakeClaude(json.dumps(answer(target_role_evidence="Objetivo: Cientista de Dados")))

    result = await analyze(fake)

    assert result.profile.target_role is None


async def test_cargo_sem_evidencia_nenhuma_fica_vazio():
    fake = FakeClaude(json.dumps(answer(target_role="Gerente", target_role_evidence=None)))

    assert (await analyze(fake)).profile.target_role is None


async def test_compara_evidencia_sem_ligar_para_maiusculas_e_espacos():
    fake = FakeClaude(json.dumps(answer(target_role_evidence="objetivo:   ANALISTA de dados")))

    assert (await analyze(fake)).profile.target_role == "Analista de Dados"


async def test_senioridade_pode_ficar_em_aberto():
    fake = FakeClaude(json.dumps(answer(seniority=None)))

    assert (await analyze(fake)).profile.seniority is None


@pytest.mark.parametrize(
    ("descricao", "fake"),
    [
        ("recusa", FakeClaude(None, stop_reason="refusal")),
        ("resposta cortada", FakeClaude('{"target_role": "Ana', stop_reason="max_tokens")),
        ("sem texto", FakeClaude(None)),
        ("JSON inválido", FakeClaude("isto não é JSON")),
        ("fora do formato", FakeClaude(json.dumps({"target_role": "x"}))),
        ("senioridade inventada", FakeClaude(json.dumps(answer(seniority="lider")))),
    ],
)
async def test_resposta_inutilizavel_vira_analysis_error(descricao, fake):
    with pytest.raises(AnalysisError):
        await analyze(fake)


def _response(status: int) -> httpx2.Response:
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx2.Response(status, request=request)


@pytest.mark.parametrize(
    "error",
    [
        anthropic.APIConnectionError(
            request=httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
        ),
        anthropic.RateLimitError("limite", response=_response(429), body=None),
        anthropic.InternalServerError("fora do ar", response=_response(500), body=None),
    ],
)
async def test_falha_temporaria_da_anthropic_vira_indisponivel(error):
    with pytest.raises(AnalysisUnavailableError):
        await analyze(FakeClaude(error=error))


async def test_pedido_recusado_pela_api_vira_analysis_error():
    error = anthropic.BadRequestError("pedido inválido", response=_response(400), body=None)

    with pytest.raises(AnalysisError, match="HTTP 400"):
        await analyze(FakeClaude(error=error))


async def test_cursos_ficam_separados_e_tambem_precisam_estar_no_curriculo():
    fake = FakeClaude(
        json.dumps(
            answer(certifications=["Linux Unhatched", "AWS Cloud Practitioner", "linux unhatched"])
        )
    )

    result = await analyze(fake)

    # O curso inventado (AWS) sai; o repetido também.
    assert result.profile.certifications == ["Linux Unhatched"]
    assert "Linux Unhatched" not in result.profile.skills


async def test_pedido_explica_o_que_vai_em_cursos_e_certificacoes():
    fake = FakeClaude(json.dumps(answer()))

    await analyze(fake)

    [request] = fake.requests
    assert "certifications" in request["output_config"]["format"]["schema"]["required"]
    assert "Não inclua formação acadêmica" in request["system"]
