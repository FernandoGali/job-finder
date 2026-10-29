import { describe, expect, it } from "vitest";

import { remotarArea, type SearchOptions, searchLinks, slugify } from "./jobSearch";

function urlOf(site: string, query: string, options: SearchOptions = {}) {
  return searchLinks(query, options).find((link) => link.site === site)?.url;
}

describe("slugify", () => {
  it("tira acentos, maiúsculas e símbolos", () => {
    expect(slugify("Análise de Dados (BI)")).toBe("analise-de-dados-bi");
    expect(slugify("  C++ / Python  ")).toBe("c-python");
  });
});

describe("searchLinks", () => {
  it("monta a busca de cada site com o termo e o local", () => {
    const options = { location: "São Paulo" };
    expect(urlOf("LinkedIn", "Analista de Dados", options)).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20Dados%22&location=S%C3%A3o%20Paulo",
    );
    expect(urlOf("Indeed", "Analista de Dados", options)).toBe(
      "https://br.indeed.com/jobs?q=title%3A(Analista%20de%20Dados)&l=S%C3%A3o%20Paulo",
    );
    expect(urlOf("Gupy", "Analista de Dados")).toBe(
      "https://portal.gupy.io/job-search/term=Analista%20de%20Dados",
    );
    expect(urlOf("Vagas.com.br", "Análise de Dados")).toBe(
      "https://www.vagas.com.br/vagas-de-analise-de-dados",
    );
    expect(urlOf("InfoJobs", "Análise de Dados")).toBe(
      "https://www.infojobs.com.br/vagas-de-emprego-analise-de-dados.aspx",
    );
    expect(urlOf("Trampos", "Analista de Dados")).toBe(
      "https://trampos.co/oportunidades?tr=Analista%20de%20Dados",
    );
    // Igual ao endereço que o próprio Remotar monta ao buscar, com área e nível.
    expect(urlOf("Remotar", "analista de dados", { level: "junior" })).toBe(
      "https://remotar.com.br/search/jobs?q=analista+de+dados&c=4&t=17",
    );
    // Sem nível escolhido e cargo sem área conhecida: só a busca.
    expect(urlOf("Remotar", "Inspetor de Solda")).toBe("https://remotar.com.br/search/jobs?q=Inspetor+de+Solda");
  });

  it("não tem mais o Glassdoor (o link não preenchia a busca)", () => {
    expect(searchLinks("Analista de Dados").map((link) => link.site)).not.toContain("Glassdoor");
  });

  it("não coloca o local quando ele está vazio", () => {
    expect(urlOf("LinkedIn", "Analista de Dados", { location: "   " })).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20Dados%22",
    );
    expect(urlOf("Indeed", "Analista de Dados")).toBe("https://br.indeed.com/jobs?q=title%3A(Analista%20de%20Dados)");
  });

  it("só remotas: filtro oficial no LinkedIn (no Brasil); os outros sites não mudam", () => {
    const remote = { remote: true };
    expect(urlOf("LinkedIn", "Analista de Dados", remote)).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20Dados%22&location=Brasil&f_WT=2",
    );
    expect(urlOf("LinkedIn", "Analista de Dados", { remote: true, location: "Minas Gerais" })).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20Dados%22&location=Minas%20Gerais&f_WT=2",
    );
    // "remoto" no termo quase zerava a busca nos outros sites: lá o filtro é feito no site.
    for (const site of ["Indeed", "Gupy", "Vagas.com.br", "InfoJobs", "Trampos", "Remotar"]) {
      expect(urlOf(site, "Analista de Dados", remote)).toBe(urlOf(site, "Analista de Dados"));
    }
  });

  it("no LinkedIn, busca a frase exata (entre aspas) sem duplicar aspas digitadas", () => {
    expect(urlOf("LinkedIn", '"Analista de BI"')).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20BI%22",
    );
    // No Indeed o termo vai no título, sem aspas nem parênteses extras.
    expect(urlOf("Indeed", "Analista de BI")).toBe("https://br.indeed.com/jobs?q=title%3A(Analista%20de%20BI)");
  });

  it("no Indeed, busca só no título e limpa parênteses e aspas digitados", () => {
    expect(urlOf("Indeed", '"Analista (BI)"')).toBe("https://br.indeed.com/jobs?q=title%3A(Analista%20BI)");
  });

  it("nível: filtro de experiência do LinkedIn e do Indeed; estágio vira tipo de vaga no Indeed", () => {
    expect(urlOf("LinkedIn", "Analista de Dados", { level: "junior" })).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20Dados%22&f_E=2%2C3",
    );
    expect(urlOf("LinkedIn", "Analista de Dados", { level: "estagio" })).toContain("&f_E=1");
    expect(urlOf("Indeed", "Analista de Dados", { level: "junior" })).toBe(
      "https://br.indeed.com/jobs?q=title%3A(Analista%20de%20Dados)&sc=0kf%3Aexplvl(ENTRY_LEVEL)%3B",
    );
    expect(urlOf("Indeed", "Analista de Dados", { level: "pleno" })).toContain("explvl(MID_LEVEL)");
    expect(urlOf("Indeed", "Analista de Dados", { level: "estagio" })).toContain("&jt=internship");
    // Sem nível escolhido, nenhum filtro; e os outros sites não mudam.
    expect(urlOf("LinkedIn", "Analista de Dados", { level: null })).not.toContain("f_E");
    expect(urlOf("Gupy", "Analista de Dados", { level: "junior" })).toBe(urlOf("Gupy", "Analista de Dados"));
  });

  it("limpa espaços repetidos e protege caracteres especiais", () => {
    expect(urlOf("LinkedIn", "  Dados   &  BI ")).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=%22Dados%20%26%20BI%22",
    );
  });

  it("não monta links sem termo de busca", () => {
    expect(searchLinks("")).toEqual([]);
    expect(searchLinks("  --- ")).toEqual([]);
  });
});

describe("Remotar: nível e área", () => {
  const remotar = (query: string, options: SearchOptions = {}) => urlOf("Remotar", query, options);

  it("põe a tag de nível de cada senioridade; gestão fica sem tag", () => {
    expect(remotar("Analista de BI", { level: "estagio" })).toContain("&t=10");
    expect(remotar("Analista de BI", { level: "pleno" })).toContain("&t=21");
    expect(remotar("Analista de BI", { level: "senior" })).toContain("&t=23");
    expect(remotar("Analista de BI", { level: "especialista" })).toContain("&t=23");
    expect(remotar("Analista de BI", { level: "gestao" })).not.toContain("t=");
  });

  it("escolhe a área pelas palavras do cargo", () => {
    expect(remotarArea("Analista de BI")).toBe("4");
    expect(remotarArea("Data Analyst")).toBe("4");
    expect(remotarArea("Desenvolvedor Mobile")).toBe("14"); // mobile antes de desenvolvedor
    expect(remotarArea("Desenvolvedor Back-end")).toBe("13");
    expect(remotarArea("Designer UX")).toBe("6"); // UX antes de design
    expect(remotarArea("Product Manager")).toBe("15");
    expect(remotarArea("Product Designer")).toBe("5"); // é cargo de design
    expect(remotarArea("Analista de Recursos Humanos")).toBe("16");
    expect(remotarArea("Analista de Marketing")).toBe("10");
    expect(remotarArea("Analista Financeiro")).toBe("1");
    expect(remotarArea("Analista de QA")).toBe("8");
  });

  it("qualidade industrial não vira QA de software, e cargo sem regra fica sem área", () => {
    expect(remotarArea("Analista de Qualidade")).toBeNull();
    expect(remotarArea("Inspetor de Qualidade")).toBeNull();
    expect(remotar("Analista de Qualidade", { level: "junior" })).toBe(
      "https://remotar.com.br/search/jobs?q=Analista+de+Qualidade&t=17",
    );
  });
});
