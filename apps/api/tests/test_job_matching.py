import pytest

from jobfinder_api.job_matching import (
    MIN_SCORE,
    JobForMatching,
    ProfileForMatching,
    job_level,
    rank_jobs,
    score_job,
    title_match,
)

PROFILE = ProfileForMatching(
    search_terms=["Analista de Dados", "Analista de BI"],
    skills=["SQL", "Python", "Power BI", "Excel", "C", "dashboards"],
    seniority="junior",
)


def job(title: str, description: str = "", job_id: str = "1") -> JobForMatching:
    return JobForMatching(
        id=job_id,
        title=title,
        company="Empresa",
        location="Brasil",
        url=f"https://exemplo.io/{job_id}",
        description=description,
    )


@pytest.mark.parametrize(
    ("title", "level"),
    [
        ("Analista de Dados Júnior", "junior"),
        ("Associate Data Engineer", "junior"),
        ("Estágio em Dados", "estagio"),
        ("Data Intern", "estagio"),
        ("Analista de Dados Pleno", "pleno"),
        ("Data Scientist II", "pleno"),
        ("Analista de Planejamento 2", "pleno"),
        ("Senior Data Scientist", "senior"),
        ("Data Engineer III", "senior"),
        ("Analista de Performance 3", "senior"),
        ("Data Specialist", "senior"),
        ("Head of Data", "gestao"),
        ("Senior Data Lead Manager", "gestao"),  # o nível mais alto vence
        ("Analista de Dados", None),
    ],
)
def test_job_level_le_o_nivel_do_titulo(title, level):
    assert job_level(title) == level


def test_cargo_em_ingles_combina_com_termo_em_portugues():
    fraction, term = title_match(["Analista de Dados"], "Data Analyst")

    assert fraction == 1
    assert term == "Analista de Dados"


def test_palavra_generica_sozinha_nao_e_cargo_parecido():
    # "Analista" sem a área (dados) não conta: suporte de TI não é análise de dados.
    assert title_match(["Analista de Dados"], "Analista de Suporte de TI") == (0.0, None)


def test_business_intelligence_e_uma_expressao_so():
    assert title_match(["Analista de Business Intelligence"], "Cyber Threat Intelligence")[0] == 0
    assert title_match(["Analista de BI"], "Business Intelligence Analyst")[0] == 1


def test_bi_combina_com_business_analyst():
    assert title_match(["Analista de BI"], "Business Analyst")[0] == 1


def test_area_sem_a_palavra_generica_vale_a_maior_parte():
    fraction, _ = title_match(["Analista de Dados"], "Data Engineer")

    assert fraction == pytest.approx(0.8)


def test_nota_e_motivo_de_uma_vaga_que_combina():
    match = score_job(
        PROFILE, job("Analista de Dados Júnior", "Usamos SQL, Python e Power BI no dia a dia.")
    )

    assert match.score == 50 + 20 + 10  # cargo + 3 de 6 competências + nível compatível
    assert match.matched_skills == ["SQL", "Python", "Power BI"]
    assert match.reasons == [
        "Cargo compatível com “Analista de Dados”",
        "Pede SQL, Python, Power BI",
        "Nível júnior, compatível com o seu",
    ]


def test_competencia_curta_precisa_ser_palavra_inteira():
    # "C" não pode valer por causa de "C++" nem de "Cobrança".
    match = score_job(PROFILE, job("Analista de Dados", "Experiência com C++ e cobrança."))

    assert "C" not in match.matched_skills


def test_motivo_resume_quando_ha_muitas_competencias():
    match = score_job(PROFILE, job("Analista de Dados", "SQL Python Power BI Excel C dashboards"))

    assert "Pede SQL, Python, Power BI, Excel, C e mais" in match.reasons


def test_vaga_de_nivel_fora_do_perfil_fica_com_nota_zero():
    match = score_job(PROFILE, job("Senior Data Analyst", "SQL, Python, Power BI, Excel"))

    assert match.score == 0
    assert "Vaga de nível sênior, fora do seu" in match.reasons


def test_vaga_sem_nivel_ganha_um_pouco():
    sem_nivel = score_job(PROFILE, job("Analista de Dados"))
    compativel = score_job(PROFILE, job("Analista de Dados Júnior"))

    assert compativel.score - sem_nivel.score == 5


def test_perfil_sem_senioridade_nao_filtra_por_nivel():
    profile = PROFILE.model_copy(update={"seniority": None})

    assert score_job(profile, job("Senior Data Analyst")).score == 50


def test_ranking_ordena_corta_pela_nota_minima_e_pelo_limite():
    jobs = [
        job("Analista de Suporte", "Atendimento", job_id="fraca"),
        job("Data Analyst", "SQL e Python", job_id="boa"),
        job("Analista de Dados Júnior", "SQL, Python, Power BI, Excel", job_id="otima"),
        job("Senior Data Analyst", "SQL, Python, Power BI, Excel", job_id="senior"),
    ]

    ranked = rank_jobs(PROFILE, jobs)

    assert [m.id for m in ranked] == ["otima", "boa"]
    assert all(m.score >= MIN_SCORE for m in ranked)
    assert [m.id for m in rank_jobs(PROFILE, jobs, limit=1)] == ["otima"]


def test_termo_so_com_palavra_generica_compara_so_ela():
    assert title_match(["Desenvolvedor"], "Desenvolvedor Python") == (1.0, "Desenvolvedor")


def test_termo_sem_palavras_uteis_e_ignorado():
    assert title_match(["de", "Analista de Dados"], "Data Analyst") == (1.0, "Analista de Dados")


def test_motivo_de_cargo_parecido():
    match = score_job(PROFILE, job("Data Engineer"))

    assert "Cargo parecido com “Analista de Dados”" in match.reasons
