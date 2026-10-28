"""Nota de compatibilidade entre uma vaga e o perfil, com o motivo de combinar.

Sem IA: a nota e o motivo saem só de fatos conferidos no texto da vaga (palavras do título,
competências encontradas na descrição, nível no título). Assim o motivo não inventa nada.

Pontos (0 a 100):
- cargo (até 50): o título da vaga tem as palavras de algum termo de busca do perfil;
- competências (até 40): quantas competências do perfil aparecem na vaga;
- nível (+10 ou +5): compatível ou não informado. Vaga de nível fora do perfil fica de fora.
"""

import re
import unicodedata
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel

MIN_SCORE = 30
MAX_RESULTS = 20
# Mais que isso não aumenta a nota: ninguém precisa bater 30 competências para combinar.
SKILLS_FOR_FULL_SCORE = 6

JobLevel = Literal["estagio", "junior", "pleno", "senior", "gestao"]
WorkMode = Literal["remoto", "hibrido", "presencial"]

# Modalidade. No título e no local, a palavra basta ("Analista (Híbrido/SP)", "Remoto").
WORK_MODE_IN_HEADER: dict[WorkMode, str] = {
    "remoto": r"\b(remoto|remota|remote|home ?office)\b",
    "hibrido": r"\b(hibrido|hibrida|hybrid)\b",
    "presencial": r"\b(presencial|on-?site)\b",
}
# Na descrição, só expressões: "auxílio home office" é benefício, não modalidade. As
# etiquetas #li-* são o padrão do LinkedIn que algumas empresas usam (ex.: Stone).
WORK_MODE_IN_DESCRIPTION: dict[WorkMode, str] = {
    "remoto": r"#li-remote|remote-first|fully remote|100% remot"
    r"|(modelo|regime|formato|trabalho) (de trabalho )?(100% )?remot",
    "hibrido": r"#li-hybrid|(modelo|regime|formato) (de trabalho )?hibrid|hybrid (model|work)",
    "presencial": r"#li-onsite|(modelo|regime|formato|rotina) (de trabalho )?presencial"
    r"|100% presencial",
}

# Equivalências PT -> EN para comparar termos em português com títulos em inglês.
SYNONYMS: dict[str, set[str]] = {
    "dados": {"data"},
    # BI no título costuma aparecer como "Business Analyst" ou "Analytics".
    "bi": {"business", "analytics"},
    "analista": {"analyst"},
    "analise": {"analysis", "analytics"},
    "cientista": {"scientist"},
    "ciencia": {"science"},
    "engenheiro": {"engineer"},
    "engenharia": {"engineering"},
    "desenvolvedor": {"developer"},
    "estagio": {"intern", "internship", "estagiario"},
    "inteligencia": {"intelligence"},
    "negocios": {"business"},
    "produto": {"product"},
    "processos": {"process", "processes"},
    "melhoria": {"improvement"},
}

STOPWORDS = {"de", "da", "do", "das", "dos", "em", "e", "a", "o", "para", "of", "and", "the"}

# Palavras genéricas de cargo: valem pouco sozinhas ("Analista de Suporte" não é "Analista de
# Dados"). O que decide é a área (dados, BI, negócios...).
ROLE_WORDS = {
    "analista",
    "analyst",
    "engenheiro",
    "engineer",
    "cientista",
    "scientist",
    "desenvolvedor",
    "developer",
    "especialista",
    "specialist",
    "assistente",
    "assistant",
    "estagio",
    "intern",
    "internship",
    "estagiario",
}
AREA_WEIGHT = 0.8

LEVEL_MARKERS: dict[JobLevel, set[str]] = {
    "estagio": {"estagio", "estagiario", "estagiaria", "intern", "internship"},
    "junior": {
        "junior",
        "jr",
        "entry",
        "trainee",
        "assistente",
        "assistant",
        "associate",
        "i",
        "1",
    },
    # Números e romanos no fim do título são níveis comuns (ex.: "Analista de Dados 2").
    "pleno": {"pleno", "pl", "mid", "ii", "2"},
    "senior": {
        "senior",
        "sr",
        "iii",
        "iv",
        "3",
        "4",
        "lead",
        "lider",
        "principal",
        "staff",
        "especialista",
        "specialist",
        "expert",
    },
    "gestao": {
        "head",
        "gerente",
        "manager",
        "coordenador",
        "coordenadora",
        "coordinator",
        "diretor",
        "diretora",
        "director",
        "supervisor",
        "supervisora",
    },
}

# Para cada senioridade do perfil, os níveis de vaga que fazem sentido.
COMPATIBLE: dict[str, set[JobLevel]] = {
    "estagio": {"estagio"},
    "junior": {"estagio", "junior"},
    "pleno": {"junior", "pleno"},
    "senior": {"pleno", "senior"},
    "especialista": {"senior"},
    "gestao": {"senior", "gestao"},
}

LEVEL_LABELS: dict[JobLevel, str] = {
    "estagio": "estágio",
    "junior": "júnior",
    "pleno": "pleno",
    "senior": "sênior",
    "gestao": "gestão",
}


class ProfileForMatching(BaseModel):
    search_terms: list[str]
    skills: list[str]
    seniority: str | None


class JobForMatching(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    description: str


class JobMatch(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    score: int
    reasons: list[str]
    matched_skills: list[str]
    work_mode: WorkMode | None = None


def normalize(text: str) -> str:
    """Minúsculas, sem acento e com espaços simples, para comparar textos.

    Os acentos saem decompondo as letras e descartando o que não é ASCII, de uma vez só (bem
    mais rápido que conferir letra por letra em descrições longas).
    """
    without_accents = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", without_accents).casefold().strip()


def _words(text: str) -> list[str]:
    # "Business Intelligence" é uma coisa só (BI); separada, "intelligence" casaria com
    # "Threat Intelligence".
    joined = re.sub(r"\bbusiness intelligence\b", "bi", normalize(text))
    return re.findall(r"[a-z0-9+#]+", joined)


def _tokens(text: str) -> list[str]:
    """Palavras normalizadas; "+" e "#" fazem parte da palavra ("c++", "c#")."""
    return re.findall(r"[a-z0-9+#]+", normalize(text))


# Textos curtos do perfil (competências e termos de busca) se repetem para cada vaga: preparados
# uma vez só. Sem isso eram ~47 mil preparações para comparar um perfil com 1.435 vagas.
@lru_cache(maxsize=4096)
def _skill_key(skill: str) -> str:
    return " ".join(_tokens(skill))


@lru_cache(maxsize=4096)
def _term_words(term: str) -> tuple[str, ...]:
    return tuple(w for w in _words(term) if w not in STOPWORDS)


class _JobText:
    """Texto da vaga preparado uma vez: palavras normalizadas separadas por um espaço.

    Conferir uma competência vira procurar " power bi " nesse texto, uma busca simples e rápida.
    Antes, cada competência normalizava e varria a descrição inteira: 517 vagas levavam 14 s.
    """

    def __init__(self, normalized_text: str) -> None:
        words = re.findall(r"[a-z0-9+#]+", normalized_text)
        self._joined = " " + " ".join(words) + " "

    def has(self, key: str) -> bool:
        return bool(key) and f" {key} " in self._joined


def job_level(title: str) -> JobLevel | None:
    """Nível que o título da vaga declara. O mais alto vence ("Senior Data Lead" é sênior)."""
    words = set(_words(title))
    for level in ("gestao", "senior", "pleno", "junior", "estagio"):
        if words & LEVEL_MARKERS[level]:
            return level
    return None


def _combined(patterns: dict[WorkMode, str]) -> re.Pattern[str]:
    """Um padrão só, com um grupo por modalidade: o texto é varrido uma vez, não três."""
    return re.compile("|".join(f"(?P<{mode}>{pattern})" for mode, pattern in patterns.items()))


_HEADER_MODES = _combined(WORK_MODE_IN_HEADER)
_DESCRIPTION_MODES = _combined(WORK_MODE_IN_DESCRIPTION)

# Toda expressão de modalidade da descrição contém uma destas palavras. Achar as palavras é uma
# busca simples; o padrão completo roda só em volta delas (varrer descrições inteiras com ele
# era metade do tempo do ranking).
_MODE_KEYWORDS = ("remot", "hibrid", "hybrid", "presencial", "#li-")
_BEFORE, _AFTER = 45, 25


def _mode_snippets(normalized: str) -> str:
    snippets = []
    for keyword in _MODE_KEYWORDS:
        start = normalized.find(keyword)
        while start != -1:
            snippets.append(normalized[max(0, start - _BEFORE) : start + len(keyword) + _AFTER])
            start = normalized.find(keyword, start + 1)
    return " | ".join(snippets)


def work_mode(
    title: str, location: str, description: str, normalized_description: str | None = None
) -> WorkMode | None:
    """Remoto, híbrido ou presencial. Título e local valem mais que a descrição.

    Se mais de uma aparece e uma delas é híbrido, vale híbrido ("modelo híbrido, com a
    flexibilidade do trabalho remoto"). Sem sinal claro, None: melhor não mostrar que chutar.
    """
    if normalized_description is None:
        normalized_description = normalize(description)
    for text, pattern in (
        (normalize(f"{title} {location}"), _HEADER_MODES),
        (_mode_snippets(normalized_description), _DESCRIPTION_MODES),
    ):
        found = {match.lastgroup for match in pattern.finditer(text)}
        if len(found) == 1:
            return found.pop()  # type: ignore[return-value]
        if "hibrido" in found:
            return "hibrido"
        if found:
            return None
    return None


def title_match(search_terms: list[str], title: str) -> tuple[float, str | None]:
    """Quanto (0 a 1) o título se parece com o melhor termo, com sinônimos PT/EN.

    As palavras da área (dados, BI...) pesam 80%; as genéricas (analista...) 20%. Sem nenhuma
    palavra da área no título, não há semelhança: "Analista de Suporte" não é "Analista de Dados".
    """
    title_words = set(_words(title))

    def found(words: list[str]) -> float:
        hits = sum(1 for w in words if ({w} | SYNONYMS.get(w, set())) & title_words)
        return hits / len(words)

    best, best_term = 0.0, None
    for term in search_terms:
        words = _term_words(term)
        area = [w for w in words if w not in ROLE_WORDS]
        role = [w for w in words if w in ROLE_WORDS]
        if area:
            area_found = found(area)
            if area_found == 0:
                continue
            fraction = AREA_WEIGHT * area_found + (1 - AREA_WEIGHT) * (found(role) if role else 1)
        elif role:
            fraction = found(role)
        else:
            continue
        if fraction > best:
            best, best_term = fraction, term
    return best, best_term


def score_job(profile: ProfileForMatching, job: JobForMatching) -> JobMatch:
    reasons: list[str] = []

    fraction, term = title_match(profile.search_terms, job.title)
    title_points = round(50 * fraction)
    if fraction == 1:
        reasons.append(f"Cargo compatível com “{term}”")
    elif fraction >= 0.5:
        reasons.append(f"Cargo parecido com “{term}”")

    # Competência = sequência de palavras inteiras ("C" não vale dentro de "C++").
    description = normalize(job.description)
    job_text = _JobText(f"{normalize(job.title)} {description}")
    matched = [skill for skill in profile.skills if job_text.has(_skill_key(skill))]
    skill_points = round(40 * min(len(matched), SKILLS_FOR_FULL_SCORE) / SKILLS_FOR_FULL_SCORE)
    if matched:
        reasons.append("Pede " + ", ".join(matched[:5]) + (" e mais" if len(matched) > 5 else ""))

    level = job_level(job.title)
    level_points = 0
    level_ok = True
    if profile.seniority in COMPATIBLE:
        if level is None:
            level_points = 5
        elif level in COMPATIBLE[profile.seniority]:
            level_points = 10
            reasons.append(f"Nível {LEVEL_LABELS[level]}, compatível com o seu")
        else:
            level_ok = False
            reasons.append(f"Vaga de nível {LEVEL_LABELS[level]}, fora do seu")

    # Vaga de outro nível não aparece, por melhor que seja o resto: era o que mais poluía a lista.
    score = max(0, min(100, title_points + skill_points + level_points)) if level_ok else 0
    return JobMatch(
        id=job.id,
        title=job.title,
        company=job.company,
        location=job.location,
        url=job.url,
        score=score,
        reasons=reasons,
        matched_skills=matched,
        work_mode=work_mode(job.title, job.location, job.description, description),
    )


def rank_jobs(
    profile: ProfileForMatching, jobs: list[JobForMatching], limit: int = MAX_RESULTS
) -> list[JobMatch]:
    """As vagas que passam da nota mínima, da maior nota para a menor."""
    matches = [score_job(profile, job) for job in jobs]
    good = [match for match in matches if match.score >= MIN_SCORE]
    good.sort(key=lambda match: (-match.score, match.title))
    return good[:limit]
