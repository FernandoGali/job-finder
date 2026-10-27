import { describe, expect, it } from "vitest";

import { searchLinks, slugify } from "./jobSearch";

function urlOf(site: string, query: string, location = "") {
  return searchLinks(query, location).find((link) => link.site === site)?.url;
}

describe("slugify", () => {
  it("tira acentos, maiúsculas e símbolos", () => {
    expect(slugify("Análise de Dados (BI)")).toBe("analise-de-dados-bi");
    expect(slugify("  C++ / Python  ")).toBe("c-python");
  });
});

describe("searchLinks", () => {
  it("monta a busca de cada site com o termo e o local", () => {
    expect(urlOf("LinkedIn", "Analista de Dados", "São Paulo")).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados&location=S%C3%A3o%20Paulo",
    );
    expect(urlOf("Indeed", "Analista de Dados", "São Paulo")).toBe(
      "https://br.indeed.com/jobs?q=Analista%20de%20Dados&l=S%C3%A3o%20Paulo",
    );
    expect(urlOf("Glassdoor", "Analista de Dados")).toBe(
      "https://www.glassdoor.com.br/Vaga/vagas.htm?sc.keyword=Analista%20de%20Dados",
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

  it("não coloca o local quando ele está vazio", () => {
    expect(urlOf("LinkedIn", "Analista de Dados", "   ")).toBe(
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados",
    );
    expect(urlOf("Indeed", "Analista de Dados")).toBe("https://br.indeed.com/jobs?q=Analista%20de%20Dados");
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
