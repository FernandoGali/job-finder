import { render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ResumeRewrite } from "@/lib/resumes";

import { RewriteCard } from "./RewriteCard";

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

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
    render(<RewriteCard resumeId="r-1" rewrite={rewrite} />);

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
    // Cada pergunta tem um campo para a resposta.
    expect(screen.getByLabelText("Quantas pessoas usavam os relatórios?")).toBeInTheDocument();
    const fixes = within(screen.getByRole("list", { name: "Pontos de alerta corrigidos" })).getAllByRole("listitem");
    expect(fixes.map((item) => item.textContent)).toEqual(["Frases de responsabilidade viraram resultados."]);
  });

  it("esconde as seções vazias", () => {
    render(
      <RewriteCard
        resumeId="r-1"
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
    expect(screen.queryByRole("form", { name: "Perguntas para fortalecer o currículo" })).not.toBeInTheDocument();
    // Reescrita antiga, feita antes dos pontos de alerta: a seção some.
    expect(screen.queryByRole("list", { name: "Pontos de alerta corrigidos" })).not.toBeInTheDocument();
  });
});
