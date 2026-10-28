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
GREENHOUSE_BOARDS: dict[str, str] = {
    "stone": "Stone",
    "quintoandar": "QuintoAndar",
    "vtex": "VTEX",
    "wildlifestudios": "Wildlife Studios",
}


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
        jobs.append(
            JobPosting(
                source="greenhouse",
                board=board,
                external_id=str(raw["id"]),
                company=raw.get("company_name") or GREENHOUSE_BOARDS.get(board, board),
                title=raw["title"].strip(),
                location=((raw.get("location") or {}).get("name") or "").strip(),
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
