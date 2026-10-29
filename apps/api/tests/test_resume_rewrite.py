import json
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest

from jobfinder_api.resume_analysis import MODEL, AnalysisError, AnalysisUnavailableError
from jobfinder_api.resume_rewrite import OUTPUT_SCHEMA, ResumeRewriter

pytestmark = pytest.mark.anyio

RESUME = """Maria Silva
Objetivo: Analista de Dados
Experiência
Analista de BI - Empresa X - 2021 a 2025
Automatizei 12 relatórios semanais com Python e SQL, reduzindo o retrabalho em 40%.
Formação
Engenharia de Produção - Universidade Y - 2015 a 2020
Ferramentas: Python, SQL, Power BI
Cursos: Linux Unhatched
"""


def answer(**overrides: Any) -> dict[str, Any]:
    return {
        "summary": "Analista com foco em dados. Automatizou 12 relatórios semanais.",
        "experiences": [
            {
                "company": "Empresa X",
                "role": "Analista de BI",
                "period": "2021 a 2025",
                "bullets": [
                    "Automatizei 12 relatórios semanais com Python e SQL.",
                    "Reduzi o retrabalho em 40%.",
                ],
            }
        ],
        "education": [
            {
                "institution": "Universidade Y",
                "course": "Engenharia de Produção",
                "period": "2015 a 2020",
            }
        ],
        "skills": ["Python", "SQL", "Power BI"],
        "certifications": ["Linux Unhatched"],
        "questions": ["Quantas pessoas usavam os relatórios?"],
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


async def rewrite(fake: FakeClaude, target: str | None = "Analista de Dados"):
    return await ResumeRewriter(fake).rewrite(RESUME, target, ["SQL", "Python"])


async def test_reescreve_e_mantem_o_que_confere_com_o_curriculo():
    result = await rewrite(FakeClaude(json.dumps(answer())))

    assert result.model == MODEL
    data = result.rewrite.model_dump()
    assert data["headline"] == "Analista de Dados"
    assert data["experiences"][0]["company"] == "Empresa X"
    assert len(data["experiences"][0]["bullets"]) == 2
    assert data["education"][0]["course"] == "Engenharia de Produção"
    assert data["skills"] == ["Python", "SQL", "Power BI"]
    assert data["questions"] == ["Quantas pessoas usavam os relatórios?"]


async def test_pedido_leva_cargo_palavras_chave_e_regras():
    fake = FakeClaude(json.dumps(answer()))

    await rewrite(fake)

    [request] = fake.requests
    assert request["model"] == "claude-opus-5-5"
    assert request["fallbacks"] == "default"
    assert request["output_config"]["format"] == {"type": "json_schema", "schema": OUTPUT_SCHEMA}
    content = request["messages"][0]["content"]
    assert "<cargo_alvo>Analista de Dados</cargo_alvo>" in content
    assert "<palavras_chave>SQL, Python</palavras_chave>" in content
    assert f"<curriculo>\n{RESUME}\n</curriculo>" in content
    assert "Nunca invente nem complete empresa, cargo, data, número" in request["system"]
    assert "faça uma pergunta em questions" in request["system"]


async def test_sem_cargo_alvo_avisa_no_pedido():
    fake = FakeClaude(json.dumps(answer()))

    result = await rewrite(fake, target=None)

    assert "<cargo_alvo>não informado</cargo_alvo>" in fake.requests[0]["messages"][0]["content"]
    assert result.rewrite.headline is None


async def test_experiencia_de_empresa_inventada_sai():
    experiences = [
        {"company": "Empresa Z", "role": "Gerente", "period": None, "bullets": ["Liderei."]},
        *answer()["experiences"],
    ]

    result = await rewrite(FakeClaude(json.dumps(answer(experiences=experiences))))

    assert [e.company for e in result.rewrite.experiences] == ["Empresa X"]


async def test_cargo_e_periodo_que_nao_conferem_ficam_em_branco():
    experiences = [
        {
            "company": "Empresa X",
            "role": "Coordenador de BI",  # promoção inventada
            "period": "2020 a 2025",  # data mudada
            "bullets": ["Estruturei dashboards."],
        }
    ]

    [experience] = (
        await rewrite(FakeClaude(json.dumps(answer(experiences=experiences))))
    ).rewrite.experiences

    assert (experience.role, experience.period) == (None, None)


async def test_frase_com_numero_que_o_curriculo_nao_tem_sai():
    experiences = [
        {
            "company": "Empresa X",
            "role": "Analista de BI",
            "period": "2021 a 2025",
            "bullets": [
                "Automatizei 12 relatórios semanais.",
                "Reduzi custos em 30%.",  # 30% não está no currículo
                "Atendi 1.500 clientes.",  # inventado
                "Organizei os indicadores da área.",
            ],
        }
    ]
    summary = "Analista de BI desde 2021. Gerou economia de R$ 2 milhões. Usa SQL."

    result = await rewrite(FakeClaude(json.dumps(answer(experiences=experiences, summary=summary))))

    assert result.rewrite.experiences[0].bullets == [
        "Automatizei 12 relatórios semanais.",
        "Organizei os indicadores da área.",
    ]
    assert result.rewrite.summary == "Analista de BI desde 2021. Usa SQL."


async def test_formacao_competencias_e_cursos_tambem_sao_conferidos():
    education = [
        {"institution": "Universidade Y", "course": "Ciência de Dados", "period": None},
        {"institution": "Harvard", "course": "MBA", "period": "2022"},
    ]
    raw = answer(
        education=education,
        skills=["Python", "Kubernetes", "python"],
        certifications=["Linux Unhatched", "AWS Cloud Practitioner"],
        questions=[f"Pergunta {i}?" for i in range(8)] + ["  "],
    )

    result = (await rewrite(FakeClaude(json.dumps(raw)))).rewrite

    assert [(e.institution, e.course) for e in result.education] == [("Universidade Y", None)]
    assert result.skills == ["Python"]
    assert result.certifications == ["Linux Unhatched"]
    assert len(result.questions) == 5


@pytest.mark.parametrize(
    "fake",
    [
        FakeClaude(None, stop_reason="refusal"),
        FakeClaude('{"summary": "x', stop_reason="max_tokens"),
        FakeClaude(None),
        FakeClaude("isto não é JSON"),
        FakeClaude(json.dumps({"summary": "x"})),
    ],
)
async def test_resposta_inutilizavel_vira_analysis_error(fake):
    with pytest.raises(AnalysisError):
        await rewrite(fake)


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
async def test_falha_temporaria_vira_indisponivel(error):
    with pytest.raises(AnalysisUnavailableError):
        await rewrite(FakeClaude(error=error))


async def test_pedido_recusado_pela_api_vira_analysis_error():
    error = anthropic.BadRequestError("pedido inválido", response=_response(400), body=None)

    with pytest.raises(AnalysisError, match="HTTP 400"):
        await rewrite(FakeClaude(error=error))
