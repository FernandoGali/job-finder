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
from typing import Literal

from pydantic import BaseModel

MIN_SCORE = 30
MAX_RESULTS = 20
# Mais que isso não aumenta a nota: ninguém precisa bater 30 competências para combinar.
SKILLS_FOR_FULL_SCORE = 6

JobLevel = Literal["estagio", "junior", "pleno", "senior", "gestao"]

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


def normalize(text: str) -> str:
    """Minúsculas, sem acento e com espaços simples, para comparar textos."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", without_accents).casefold().strip()


def _words(text: str) -> list[str]:
    # "Business Intelligence" é uma coisa só (BI); separada, "intelligence" casaria com
    # "Threat Intelligence".
    joined = re.sub(r"\bbusiness intelligence\b", "bi", normalize(text))
    return re.findall(r"[a-z0-9+#]+", joined)


def _has_phrase(phrase: str, text: str) -> bool:
    """A expressão aparece como palavras inteiras ("C" não vale dentro de "C++")."""
    needle = normalize(phrase)
    pattern = rf"(?<![\w+#]){re.escape(needle)}(?![\w+#])"
    return bool(needle) and re.search(pattern, normalize(text)) is not None


def job_level(title: str) -> JobLevel | None:
    """Nível que o título da vaga declara. O mais alto vence ("Senior Data Lead" é sênior)."""
    words = set(_words(title))
    for level in ("gestao", "senior", "pleno", "junior", "estagio"):
        if words & LEVEL_MARKERS[level]:
            return level
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
        words = [w for w in _words(term) if w not in STOPWORDS]
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

    text = f"{job.title}\n{job.description}"
    matched = [skill for skill in profile.skills if _has_phrase(skill, text)]
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
    )


def rank_jobs(
    profile: ProfileForMatching, jobs: list[JobForMatching], limit: int = MAX_RESULTS
) -> list[JobMatch]:
    """As vagas que passam da nota mínima, da maior nota para a menor."""
    matches = [score_job(profile, job) for job in jobs]
    good = [match for match in matches if match.score >= MIN_SCORE]
    good.sort(key=lambda match: (-match.score, match.title))
    return good[:limit]
