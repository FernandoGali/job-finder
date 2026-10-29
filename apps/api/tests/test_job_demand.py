from jobfinder_api.job_demand import MAX_ITEMS, MIN_JOBS, VOCABULARY, market_demand, pareto
from jobfinder_api.job_matching import JobForMatching


def job(i: int, title: str, description: str) -> JobForMatching:
    return JobForMatching(
        id=str(i),
        title=title,
        company="Stone",
        location="São Paulo",
        url=f"https://job-boards.greenhouse.io/stone/jobs/{i}",
        description=description,
    )


DATA_JOBS = [
    job(1, "Analista de Dados Júnior", "SQL, Python e Power BI. Vale refeição."),
    job(2, "Data Analyst I", "Advanced SQL and Python. English."),
    job(3, "Analista de Dados", "SQL e Excel avançado. Inglês."),
    job(4, "Analista de Dados Pleno", "SQL, Power BI, estatística."),
    job(5, "Analista de Dados Sênior", "PowerBI, SQL."),
]
OTHER_JOBS = [
    job(6, "Analista de Suporte", "SQL, SQL, SQL."),  # outro cargo: não conta
    job(7, "Engenheiro de Dados", "Spark e Airflow."),  # "Dados", mas não é analista
]


def test_conta_em_quantas_vagas_do_cargo_cada_item_aparece():
    [demand] = market_demand(["Analista de Dados"], DATA_JOBS + OTHER_JOBS, ["SQL", "Excel"])

    assert demand.role == "Analista de Dados"
    assert demand.jobs == 5
    items = {item.name: item for item in demand.items}
    assert (items["SQL"].jobs, items["SQL"].share) == (5, 100)
    # "PowerBI" junto conta como Power BI; "Inglês" e "English" são o mesmo item.
    assert (items["Power BI"].jobs, items["Power BI"].share) == (3, 60)
    assert items["Python"].jobs == 2
    # Benefício não é item ("Vale refeição" não entra).
    assert all(item.name in VOCABULARY for item in demand.items)


def test_marca_o_que_o_curriculo_ja_cita():
    [demand] = market_demand(["Analista de Dados"], DATA_JOBS, ["SQL", "Excel avançado", "PowerBI"])

    have = {item.name: item.in_resume for item in demand.items}
    assert have["SQL"] is True
    assert have["Power BI"] is True  # escrito de outro jeito no currículo
    assert have["Python"] is False


def test_termos_do_curriculo_nao_se_juntam():
    # "Power" e "BI" em competências separadas não viram "Power BI".
    [demand] = market_demand(["Analista de Dados"], DATA_JOBS, ["Power", "BI"])

    assert {item.name: item.in_resume for item in demand.items}["Power BI"] is False


def test_poucas_vagas_nao_viram_porcentagem():
    [demand] = market_demand(["Analista de Dados"], DATA_JOBS[: MIN_JOBS - 1], ["SQL"])

    assert demand.jobs == MIN_JOBS - 1
    assert demand.items == []


def test_um_resultado_por_cargo_na_ordem_pedida():
    roles = ["Analista de BI", "Analista de Dados"]

    assert [d.role for d in market_demand(roles, DATA_JOBS, [])] == roles


def test_pareto_pega_os_mais_citados_ate_80_por_cento():
    # Total 100: SQL (50) + Python (25) = 75, ainda abaixo de 80; Excel (15) cruza a linha e entra.
    counts = {"SQL": 50, "Python": 25, "Excel": 15, "Tableau": 10, "Looker": 0}

    assert pareto(counts) == ["SQL", "Python", "Excel"]


def test_pareto_empata_pelo_nome_e_tem_limite():
    counts = {f"Item {i:02}": 1 for i in range(30)}

    chosen = pareto(counts)

    assert len(chosen) == MAX_ITEMS
    assert chosen[:2] == ["Item 00", "Item 01"]


def test_pareto_sem_citacoes():
    assert pareto({"SQL": 0}) == []


def test_so_conta_vagas_do_mesmo_nivel_e_as_sem_nivel():
    jobs = [
        *(job(10 + i, "Analista de Dados Júnior", "SQL.") for i in range(3)),
        job(20, "Data Analyst", "SQL e Excel."),  # sem nível no título: conta
        job(21, "Analista de Dados", "SQL."),  # sem nível no título: conta
        *(job(30 + i, "Analista de Dados Sênior", "SQL e Machine Learning.") for i in range(4)),
        job(40, "Estágio em Análise de Dados", "SQL."),  # estágio não é júnior
    ]

    [demand] = market_demand(["Analista de Dados"], jobs, [], "junior")

    assert (demand.jobs, demand.level) == (5, "júnior")
    assert "Machine Learning" not in [item.name for item in demand.items]


def test_especialista_conta_vagas_senior_e_sem_senioridade_conta_todas():
    jobs = [job(i, "Analista de Dados Sênior", "SQL.") for i in range(5)]

    [especialista] = market_demand(["Analista de Dados"], jobs, [], "especialista")
    [sem_nivel] = market_demand(["Analista de Dados"], DATA_JOBS, [], None)

    assert (especialista.jobs, especialista.level) == (5, "sênior")
    assert (sem_nivel.jobs, sem_nivel.level) == (5, None)
