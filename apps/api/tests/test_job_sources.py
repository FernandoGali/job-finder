import httpx
import pytest

from jobfinder_api.job_sources import (
    JobSourceError,
    fetch_greenhouse,
    fetch_lever,
    html_to_text,
    is_brazil_location,
    lever_title,
    parse_greenhouse,
    parse_lever,
)

# Formato real da Greenhouse (conferido em 28/10/2026), com a descrição codificada duas vezes.
PAYLOAD = {
    "jobs": [
        {
            "id": 4433716009,
            "title": " Analista de Dados ",
            "company_name": "QuintoAndar",
            "location": {"name": "Brasil"},
            "absolute_url": "https://job-boards.greenhouse.io/quintoandar/jobs/4433716009",
            "content": "&amp;lt;p&amp;gt;Sobre &amp;amp;nbsp;n&amp;oacute;s&amp;lt;/p&amp;gt;"
            "&amp;lt;ul&amp;gt;&amp;lt;li&amp;gt;SQL&amp;lt;/li&amp;gt;"
            "&amp;lt;li&amp;gt;Python&amp;lt;/li&amp;gt;&amp;lt;/ul&amp;gt;",
            "first_published": "2026-10-01T10:00:00-03:00",
            "updated_at": "2026-10-13T14:02:02-04:00",
        },
        {
            "id": 2,
            "title": "Vaga sem link seguro",
            "location": None,
            "absolute_url": "http://inseguro.example/2",
            "content": "",
        },
    ]
}


def test_html_to_text_decodifica_e_mantem_paragrafos():
    assert html_to_text(PAYLOAD["jobs"][0]["content"]) == "Sobre nós\nSQL\nPython"


def test_parse_greenhouse_normaliza_a_vaga_e_descarta_link_inseguro():
    [job] = parse_greenhouse("quintoandar", PAYLOAD)

    assert job.source == "greenhouse"
    assert job.board == "quintoandar"
    assert job.external_id == "4433716009"
    assert job.company == "QuintoAndar"
    assert job.title == "Analista de Dados"
    assert job.location == "Brasil"
    assert job.description == "Sobre nós\nSQL\nPython"
    assert job.url == "https://job-boards.greenhouse.io/quintoandar/jobs/4433716009"
    assert job.updated_at is not None


def test_parse_greenhouse_usa_o_nome_da_lista_quando_falta_a_empresa():
    payload = {"jobs": [{**PAYLOAD["jobs"][0], "company_name": None}]}

    assert parse_greenhouse("vtex", payload)[0].company == "VTEX"


def test_parse_greenhouse_aceita_quadro_vazio():
    assert parse_greenhouse("nubank", {"jobs": []}) == []


@pytest.mark.anyio
async def test_fetch_greenhouse_pede_a_descricao_completa():
    requests: list[httpx.Request] = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=PAYLOAD)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        jobs = await fetch_greenhouse(http, "quintoandar")

    assert len(jobs) == 1
    assert (
        str(requests[0].url)
        == "https://boards-api.greenhouse.io/v1/boards/quintoandar/jobs?content=true"
    )


def _offline(request):
    raise httpx.ConnectError("sem rede")


@pytest.mark.anyio
@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(404, json={"status": 404}),
        lambda request: httpx.Response(200, text="isto nao e json"),
        _offline,
    ],
)
async def test_fetch_greenhouse_falha_vira_job_source_error(handler):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(JobSourceError):
            await fetch_greenhouse(http, "quintoandar")


@pytest.mark.parametrize(
    ("location", "kept"),
    [
        ("São Paulo, São Paulo, Brazil", True),
        ("Brasil", True),
        ("Jundiaí", True),  # cidade brasileira fora de qualquer lista: fica
        ("Remoto", True),
        ("", True),
        ("Mexico City, Mexico City, Mexico", False),
        ("UK (London - Hybrid)", False),
        ("US (Remote)", False),
        ("Miami, FL", False),
        ("Spain - Boadilla del Monte, Madrid", False),
        ("Argentina; São Paulo, Brazil", True),  # cita o Brasil: fica
    ],
)
def test_so_vagas_no_brasil(location, kept):
    assert is_brazil_location(location) is kept


def test_parse_greenhouse_descarta_vagas_fora_do_brasil():
    payload = {"jobs": [{**PAYLOAD["jobs"][0], "location": {"name": "Mexico City, Mexico"}}]}

    assert parse_greenhouse("quintoandar", payload) == []


# Formato real da Lever (conferido em 29/10/2026).
LEVER_PAYLOAD = [
    {
        "id": "4a84bde1",
        "text": "[ Job -  32032] Senior Data Analyst, Brazil",
        "country": "BR",
        "categories": {"location": "Campinas, Brazil", "commitment": "Homeoffice"},
        "descriptionPlain": "Sobre a vaga",
        "lists": [{"text": "Requisitos", "content": "<li>SQL</li><li>Power BI</li>"}],
        "additionalPlain": "Benefícios",
        "hostedUrl": "https://jobs.lever.co/ciandt/4a84bde1",
        "createdAt": 1790779378271,
    },
    {  # fora do Brasil pelo país
        "id": "2",
        "text": "Data Product Manager, Colombia",
        "country": "CO",
        "categories": {"location": "Colombia"},
        "hostedUrl": "https://jobs.lever.co/ciandt/2",
    },
    {  # sem país: vale o local
        "id": "3",
        "text": "Analista de CRM",
        "categories": {"location": "São Paulo"},
        "hostedUrl": "https://jobs.lever.co/neon/3",
    },
    {  # sem país e local de fora
        "id": "4",
        "text": "Engineer",
        "categories": {"location": "Mexico City"},
        "hostedUrl": "https://jobs.lever.co/neon/4",
    },
    {"id": "5", "text": "Sem link seguro", "country": "BR", "hostedUrl": "http://x/5"},
]


@pytest.mark.parametrize(
    ("raw", "clean"),
    [
        (
            "[ job -  32032] Senior Fullstack Developer ( Java + Angular ), Brazil",
            "Senior Fullstack Developer ( Java + Angular )",
        ),
        ("[29753] - Senior Data Visualization Engineer", "Senior Data Visualization Engineer"),
        ("Analista de Dados, Brasil", "Analista de Dados"),
        ("Analista de CRM Sênior", "Analista de CRM Sênior"),
    ],
)
def test_lever_title_tira_codigo_e_pais(raw, clean):
    assert lever_title(raw) == clean


def test_parse_lever_normaliza_e_so_fica_com_vagas_no_brasil():
    jobs = parse_lever("ciandt", LEVER_PAYLOAD)

    assert [job.external_id for job in jobs] == ["4a84bde1", "3"]
    job = jobs[0]
    assert job.source == "lever"
    assert job.company == "CI&T"
    assert job.title == "Senior Data Analyst"
    assert job.location == "Campinas, Brazil"
    assert job.description.splitlines() == [
        "Sobre a vaga",
        "Requisitos",
        "SQL",
        "Power BI",
        "Benefícios",
    ]
    assert job.url == "https://jobs.lever.co/ciandt/4a84bde1"
    assert job.published_at is not None and job.published_at.year == 2026
    assert jobs[1].published_at is None


@pytest.mark.anyio
async def test_fetch_lever_pede_o_json_da_empresa():
    requests: list[httpx.Request] = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=LEVER_PAYLOAD)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        jobs = await fetch_lever(http, "ciandt")

    assert len(jobs) == 2
    assert str(requests[0].url) == "https://api.lever.co/v0/postings/ciandt?mode=json"


@pytest.mark.anyio
@pytest.mark.parametrize(
    "handler",
    [
        lambda request: httpx.Response(404, json={"ok": False}),
        lambda request: httpx.Response(200, json={"ok": False, "error": "Document not found"}),
        _offline,
    ],
)
async def test_fetch_lever_falha_vira_job_source_error(handler):
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        with pytest.raises(JobSourceError, match="lever/ciandt"):
            await fetch_lever(http, "ciandt")
