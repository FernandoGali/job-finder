import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ProfileCard } from "./ProfileCard";

describe("ProfileCard", () => {
  it("mostra cargo, senioridade, competências e resumo", () => {
    render(
      <ProfileCard
        profile={{
          target_role: "Analista de Dados",
          seniority: "senior",
          skills: ["Python", "SQL"],
          certifications: ["Fundamentos do Python 1"],
          search_terms: [],
          summary: "Seis anos com dados.",
        }}
      />,
    );

    const card = screen.getByRole("region", { name: "Perfil lido pela IA" });
    expect(card).toHaveTextContent("Cargo-alvoAnalista de Dados");
    expect(card).toHaveTextContent("SenioridadeSênior");
    const skills = within(screen.getByRole("list", { name: "Competências" })).getAllByRole("listitem");
    expect(skills.map((item) => item.textContent)).toEqual(["Python", "SQL"]);
    expect(card).toHaveTextContent("Seis anos com dados.");
    const courses = within(screen.getByRole("list", { name: "Cursos e certificações" })).getAllByRole("listitem");
    expect(courses.map((item) => item.textContent)).toEqual(["Fundamentos do Python 1"]);
  });

  it("diz quando a IA não identificou algo, em vez de inventar", () => {
    render(<ProfileCard profile={{ target_role: null, seniority: null, skills: [], certifications: [], search_terms: [], summary: "" }} />);

    const card = screen.getByRole("region", { name: "Perfil lido pela IA" });
    expect(card).toHaveTextContent("Não identificado no currículo");
    expect(card).toHaveTextContent("Não deu para deduzir");
    expect(card).toHaveTextContent("Nenhuma competência identificada.");
    expect(screen.queryByRole("list", { name: "Cursos e certificações" })).not.toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Cargos sugeridos" })).not.toBeInTheDocument();
  });

  it("mostra os cargos sugeridos com o trecho do currículo e as palavras-chave", () => {
    render(
      <ProfileCard
        profile={{
          target_role: "Analista de Dados",
          seniority: "pleno",
          skills: ["SQL"],
          certifications: [],
          suggested_roles: [
            { title: "Analista de Dados", evidence: "Objetivo: Analista de Dados", keywords: ["SQL", "Python"] },
            { title: "Analista de BI", evidence: null, keywords: [] },
          ],
          search_terms: ["Analista de Dados", "Analista de BI"],
          summary: "",
        }}
      />,
    );

    const roles = within(screen.getByRole("list", { name: "Cargos sugeridos" })).getAllByRole("listitem");
    expect(roles[0]).toHaveTextContent("Analista de Dados");
    expect(roles[0]).toHaveTextContent("No currículo: “Objetivo: Analista de Dados”");
    const keywords = within(screen.getByRole("list", { name: "Palavras-chave para Analista de Dados" })).getAllByRole(
      "listitem",
    );
    expect(keywords.map((item) => item.textContent)).toEqual(["SQL", "Python"]);
    // Sem evidência conferida, não aparece trecho nenhum.
    expect(screen.getByText("Analista de BI").parentElement).not.toHaveTextContent("No currículo");
  });
});
