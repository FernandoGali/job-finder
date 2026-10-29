"""O que as vagas pedem para cada cargo sugerido: os itens mais citados nas vagas coletadas.

Sem IA: é contagem em vagas reais. Para cada cargo, entram as vagas cujo título combina por
inteiro com ele (a mesma comparação do ranking). Em cada vaga, procura-se cada item de uma
lista fechada de ferramentas, linguagens, métodos e idiomas: palavras soltas da descrição não
servem, porque as mais comuns são benefícios ("vale refeição", "auxílio creche").

Só contam as vagas do nível da pessoa e as que não dizem o nível no título: para um perfil
júnior, o que uma vaga sênior pede (ex.: Machine Learning) distorce a conta.

Depois, um Pareto: do item mais citado para o menos, entram os itens até somarem 80% de todas
as citações, no máximo 10. Cada item diz em quantas vagas aparece e se o currículo já o cita.
"""

from pydantic import BaseModel

from jobfinder_api.job_matching import (
    LEVEL_LABELS,
    JobForMatching,
    JobLevel,
    _JobText,
    _skill_key,
    job_level,
    normalize,
    title_match,
)

PARETO_SHARE = 0.8
MAX_ITEMS = 10
# Com menos vagas que isso, a porcentagem engana (1 vaga em 2 vira "50%").
MIN_JOBS = 5

# Senioridade do perfil -> nível de vaga equivalente. Especialista é o sênior dos títulos.
SAME_LEVEL: dict[str, JobLevel] = {
    "estagio": "estagio",
    "junior": "junior",
    "pleno": "pleno",
    "senior": "senior",
    "especialista": "senior",
    "gestao": "gestao",
}

# Nome mostrado -> formas como aparece nas vagas. Comparação por palavras inteiras, sem acento
# e sem maiúsculas. Ficam de fora nomes ambíguos demais para contar ("R", "Go", ".NET").
VOCABULARY: dict[str, tuple[str, ...]] = {
    # Dados e BI
    "SQL": ("sql",),
    "Python": ("python", "pyspark"),
    "Excel": ("excel",),
    "Power BI": ("power bi", "powerbi"),
    "DAX": ("dax",),
    "Power Query": ("power query",),
    "Tableau": ("tableau",),
    "Looker": ("looker",),
    "Qlik": ("qlik", "qlikview", "qlik sense"),
    "Metabase": ("metabase",),
    "Google Sheets": ("google sheets", "planilhas google"),
    "VBA": ("vba",),
    "Estatística": ("estatistica", "statistics", "statistical"),
    "Machine Learning": ("machine learning", "aprendizado de maquina"),
    "Inteligência Artificial": (
        "inteligencia artificial",
        "artificial intelligence",
        "genai",
        "llm",
        "llms",
    ),
    "ETL": ("etl", "elt"),
    "Modelagem de dados": ("modelagem de dados", "data modeling", "data modelling"),
    "Data Warehouse": ("data warehouse", "data lake", "lakehouse"),
    "Spark": ("spark", "pyspark"),
    "Pandas": ("pandas",),
    "Databricks": ("databricks",),
    "BigQuery": ("bigquery",),
    "Snowflake": ("snowflake",),
    "dbt": ("dbt",),
    "Airflow": ("airflow",),
    "SAS": ("sas",),
    "Google Analytics": ("google analytics",),
    # Nuvem e desenvolvimento
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "GCP": ("gcp", "google cloud"),
    "Git": ("git", "github", "gitlab"),
    "APIs REST": ("api rest", "apis rest", "rest api", "rest apis", "restful"),
    "Java": ("java",),
    "JavaScript": ("javascript",),
    "TypeScript": ("typescript",),
    "React": ("react", "reactjs"),
    "Node.js": ("node js", "nodejs"),
    "C#": ("c#",),
    "Kotlin": ("kotlin",),
    "Swift": ("swift",),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes", "k8s"),
    "Linux": ("linux",),
    # Processos e gestão
    "Indicadores (KPIs)": ("kpi", "kpis", "indicadores de desempenho"),
    "OKR": ("okr", "okrs"),
    "Metodologias ágeis": ("agil", "ageis", "agile", "scrum", "kanban"),
    "Jira": ("jira",),
    "Gestão de projetos": ("gestao de projetos", "project management"),
    "Mapeamento de processos": ("mapeamento de processos", "process mapping", "bpmn"),
    "Melhoria contínua": ("melhoria continua", "continuous improvement", "kaizen"),
    "Lean": ("lean",),
    "Six Sigma": ("six sigma", "seis sigma"),
    "PDCA": ("pdca",),
    "RPA": ("rpa",),
    "SAP": ("sap",),
    "ERP": ("erp",),
    "Salesforce": ("salesforce",),
    "CRM": ("crm",),
    "Figma": ("figma",),
    # Idiomas
    "Inglês": ("ingles", "english"),
    "Espanhol": ("espanhol", "spanish"),
}


class DemandItem(BaseModel):
    name: str
    jobs: int
    share: int  # porcentagem das vagas do cargo que citam o item
    in_resume: bool


class RoleDemand(BaseModel):
    role: str
    jobs: int
    level: str | None  # nível das vagas contadas ("júnior"); None quando entram todos
    items: list[DemandItem]


def _cites(text: _JobText, name: str) -> bool:
    return any(text.has(_skill_key(alias)) for alias in VOCABULARY[name])


def pareto(counts: dict[str, int]) -> list[str]:
    """Os itens mais citados até somarem 80% das citações (o que cruza a linha entra)."""
    ranked = sorted((name for name in counts if counts[name] > 0), key=lambda n: (-counts[n], n))
    total = sum(counts[name] for name in ranked)
    chosen: list[str] = []
    covered = 0
    for name in ranked[:MAX_ITEMS]:
        if covered >= PARETO_SHARE * total:
            break
        chosen.append(name)
        covered += counts[name]
    return chosen


def role_demand(
    role: str, jobs: list[JobForMatching], resume_terms: list[str], seniority: str | None = None
) -> RoleDemand:
    level = SAME_LEVEL.get(seniority or "")
    texts = [
        _JobText(normalize(f"{job.title} {job.description}"))
        for job in jobs
        if title_match([role], job.title)[0] == 1
        and (level is None or job_level(job.title) in (level, None))
    ]
    label = LEVEL_LABELS[level] if level else None
    if len(texts) < MIN_JOBS:
        return RoleDemand(role=role, jobs=len(texts), level=label, items=[])

    counts = {name: sum(1 for text in texts if _cites(text, name)) for name in VOCABULARY}
    # Cada termo do currículo separado, para não juntar o fim de um com o começo de outro.
    resume = [_JobText(normalize(term)) for term in resume_terms]
    return RoleDemand(
        role=role,
        jobs=len(texts),
        level=label,
        items=[
            DemandItem(
                name=name,
                jobs=counts[name],
                share=round(100 * counts[name] / len(texts)),
                in_resume=any(_cites(term, name) for term in resume),
            )
            for name in pareto(counts)
        ],
    )


def resume_terms(profile: dict) -> list[str]:
    """O que o currículo cita, para marcar os itens que a pessoa já tem: competências e
    palavras-chave dos cargos sugeridos. Cursos não entram: "Fundamentos do Python 1" não
    quer dizer que a pessoa usa Python."""
    roles = profile.get("suggested_roles") or []
    return [
        *(profile.get("skills") or []),
        *(keyword for role in roles for keyword in role.get("keywords", [])),
    ]


def market_demand(
    roles: list[str],
    jobs: list[JobForMatching],
    resume_terms: list[str],
    seniority: str | None = None,
) -> list[RoleDemand]:
    return [role_demand(role, jobs, resume_terms, seniority) for role in roles]
