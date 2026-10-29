import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { ResumeRewrite } from "@/lib/resumes";

import { RewriteCard } from "./RewriteCard";

const rewrite: ResumeRewrite = {
  headline: "Analista de Dados",
  summary: "Analista com foco em dados.",
  experiences: [
    {
      company: "Empresa X",
      role: "Analista de BI",
      period: "2021 a 2025",
      bullets: ["Automatizei 12 relatórios semanais.", "Estruturei dashboards."],
    },
    { company: "Empresa Y", role: null, period: null, bullets: ["Apoiei a área."] },
  ],
  education: [{ institution: "Universidade Y", course: "Engenharia de Produção", period: null }],
  skills: ["SQL", "Python"],
  certifications: ["Linux Unhatched"],
  fixes: ["Frases de responsabilidade viraram resultados."],
  questions: ["Quantas pessoas usavam os relatórios?"],
};

describe("RewriteCard", () => {
  it("mostra o currículo em seções padrão e as perguntas", () => {
    render(<RewriteCard rewrite={rewrite} />);

    const card = screen.getByRole("region", { name: "Currículo reescrito para ATS" });
    expect(card).toHaveTextContent("Analista de Dados");
    for (const title of ["Resumo", "Experiência", "Formação", "Competências", "Cursos e certificações"]) {
      expect(within(card).getByRole("heading", { name: title })).toBeInTheDocument();
    }
    expect(card).toHaveTextContent("Analista de BI · Empresa X · 2021 a 2025");
    expect(card).toHaveTextContent("Automatizei 12 relatórios semanais.");
    // Cargo e período que não conferiram com o currículo simplesmente não aparecem.
    expect(screen.getByText("Empresa Y")).toBeInTheDocument();
    expect(card).toHaveTextContent("Engenharia de Produção · Universidade Y");
    expect(card).toHaveTextContent("SQL · Python");
    const questions = within(screen.getByRole("list", { name: "Perguntas para fortalecer o currículo" })).getAllByRole(
      "listitem",
    );
    expect(questions.map((item) => item.textContent)).toEqual(["Quantas pessoas usavam os relatórios?"]);
    const fixes = within(screen.getByRole("list", { name: "Pontos de alerta corrigidos" })).getAllByRole("listitem");
    expect(fixes.map((item) => item.textContent)).toEqual(["Frases de responsabilidade viraram resultados."]);
  });

  it("esconde as seções vazias", () => {
    render(
      <RewriteCard
        rewrite={{
          headline: null,
          summary: "",
          experiences: [],
          education: [],
          skills: [],
          certifications: [],
          questions: [],
        }}
      />,
    );

    expect(screen.queryByRole("heading", { name: "Resumo" })).not.toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Experiência" })).not.toBeInTheDocument();
    expect(screen.queryByRole("list", { name: "Perguntas para fortalecer o currículo" })).not.toBeInTheDocument();
    // Reescrita antiga, feita antes dos pontos de alerta: a seção some.
    expect(screen.queryByRole("list", { name: "Pontos de alerta corrigidos" })).not.toBeInTheDocument();
  });
});
