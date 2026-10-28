"""Fontes de vagas. Hoje: quadros públicos da Greenhouse de empresas escolhidas.

Checagem de 28/10/2026 (regra 3): a documentação diz que "Job Board data is publicly
available, so authentication is not required for any GET endpoints", e o robots.txt da API
só bloqueia /embed/. Nenhum login, proxy ou contorno de limite.
"""

import html
import re
from datetime import datetime

import httpx
from pydantic import BaseModel

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards"

# Empresas cujo quadro de vagas na Greenhouse é lido. Chave: o "board token" da URL.
# Conferidas em 29/10/2026 (vagas no Brasil entre parênteses). De fora: "juno" (vagas só nos
# EUA, provavelmente outra empresa), "wise" (outra empresa), nubank e flash (quadro vazio).
GREENHOUSE_BOARDS: dict[str, str] = {
    "stone": "Stone",  # 369
    "btgpactual": "BTG Pactual",  # 250
    "c6bank": "C6 Bank",  # 156
    "inter": "Inter",  # 144
    "xpinc": "XP Inc.",  # 94
    "agibank": "Agibank",  # 91
    "quintoandar": "QuintoAndar",  # 85
    "gympass": "Wellhub",  # 52
    "arcoeducacao": "Arco Educação",  # 43
    "ebanx": "EBANX",  # 27
    "vtex": "VTEX",  # 19
    "jusbrasil": "Jusbrasil",  # 17
    "wildlifestudios": "Wildlife Studios",  # 14
    "getnet": "Getnet",  # 11
    "bancopan": "Banco PAN",  # 11
    "rdstation": "RD Station",  # 9
}

# O Job Finder é para vagas no Brasil. São empresas brasileiras, então vale o contrário de uma
# lista de cidades (que deixaria Jundiaí ou Paranaguá de fora): só sai o que é claramente de
# fora. Se o local cita o Brasil junto com outro país, a vaga fica.
BRAZIL = re.compile(r"\bbra[sz]il\b", re.IGNORECASE)
ABROAD = re.compile(
    r"\b(mexico|m[eé]xico|cdmx|argentina|buenos aires|uruguay|uruguai|montevideo|chile|"
    r"santiago de chile|colombia|col[oô]mbia|bogot[aá]|medell[ií]n|peru|lima|"
    r"united states|usa|us|eua|miami|florida|fl|new york|ny|manhattan|san francisco|"
    r"canada|uk|united kingdom|london|ireland|dublin|germany|berlin|munich|"
    r"netherlands|amsterdam|spain|espanha|madrid|barcelona|boadilla|italy|milan|"
    r"portugal|lisbon|lisboa|porto, portugal|france|paris|poland|warsaw|romania|bucharest|"
    r"india|singapore|china|shanghai|japan|tokyo|australia)\b",
    re.IGNORECASE,
)


def is_brazil_location(location: str) -> bool:
    return bool(BRAZIL.search(location)) or not ABROAD.search(location)


class JobPosting(BaseModel):
    """Vaga no formato do Job Finder, igual para qualquer fonte."""

    source: str
    board: str
    external_id: str
    company: str
    title: str
    location: str
    description: str
    url: str
    published_at: datetime | None
    updated_at: datetime | None


class JobSourceError(Exception):
    """A fonte não respondeu ou respondeu algo inesperado."""


def html_to_text(content: str) -> str:
    """A Greenhouse manda a descrição como HTML codificado em entidades (às vezes duas vezes)."""
    text = html.unescape(html.unescape(content))
    text = re.sub(r"<(br|/p|/li|/h\d|/div)\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    # Entidades do próprio texto (ex.: &nbsp;), que só aparecem depois de tirar as tags.
    text = html.unescape(text)
    lines = (re.sub(r"[ \t\u00a0]+", " ", line).strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def parse_greenhouse(board: str, payload: dict) -> list[JobPosting]:
    jobs = []
    for raw in payload.get("jobs", []):
        url = raw.get("absolute_url") or ""
        if not url.startswith("https://"):
            continue  # sem link seguro para a candidatura, a vaga não serve
        location = ((raw.get("location") or {}).get("name") or "").strip()
        if not is_brazil_location(location):
            continue
        jobs.append(
            JobPosting(
                source="greenhouse",
                board=board,
                external_id=str(raw["id"]),
                company=raw.get("company_name") or GREENHOUSE_BOARDS.get(board, board),
                title=raw["title"].strip(),
                location=location,
                description=html_to_text(raw.get("content") or ""),
                url=url,
                published_at=raw.get("first_published"),
                updated_at=raw.get("updated_at"),
            )
        )
    return jobs


async def fetch_greenhouse(http: httpx.AsyncClient, board: str) -> list[JobPosting]:
    try:
        response = await http.get(f"{GREENHOUSE_API}/{board}/jobs", params={"content": "true"})
        response.raise_for_status()
        return parse_greenhouse(board, response.json())
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        raise JobSourceError(f"greenhouse/{board}: {exc}") from exc
