import { describe, expect, it } from "vitest";

import { type SearchOptions, searchLinks, slugify } from "./jobSearch";

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
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados&location=S%C3%A3o%20Paulo",
    );
    expect(urlOf("Indeed", "Analista de Dados", options)).toBe(
      "https://br.indeed.com/jobs?q=Analista%20de%20Dados&l=S%C3%A3o%20Paulo",
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
  });

  it("não tem mais o Glassdoor (o link não preenchia a busca)", () => {
    expect(searchLinks("Analista de Dados").map((link) => link.site)).not.toContain("Glassdoor");
  });

  it("não coloca o local quando ele está vazio", () => {
    expect(urlOf("LinkedIn", "Analista de Dados", { location: "   " })).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados",
    );
    expect(urlOf("Indeed", "Analista de Dados")).toBe("https://br.indeed.com/jobs?q=Analista%20de%20Dados");
  });

  it("só remotas: filtro oficial no LinkedIn (no Brasil); os outros sites não mudam", () => {
    const remote = { remote: true };
    expect(urlOf("LinkedIn", "Analista de Dados", remote)).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados&location=Brasil&f_WT=2",
    );
    expect(urlOf("LinkedIn", "Analista de Dados", { remote: true, location: "Minas Gerais" })).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados&location=Minas%20Gerais&f_WT=2",
    );
    // "remoto" no termo quase zerava a busca nos outros sites: lá o filtro é feito no site.
    for (const site of ["Indeed", "Gupy", "Vagas.com.br", "InfoJobs", "Trampos"]) {
      expect(urlOf(site, "Analista de Dados", remote)).toBe(urlOf(site, "Analista de Dados"));
    }
  });

  it("limpa espaços repetidos e protege caracteres especiais", () => {
    expect(urlOf("LinkedIn", "  Dados   &  BI ")).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=Dados%20%26%20BI",
    );
  });

  it("não monta links sem termo de busca", () => {
    expect(searchLinks("")).toEqual([]);
    expect(searchLinks("  --- ")).toEqual([]);
  });
});
