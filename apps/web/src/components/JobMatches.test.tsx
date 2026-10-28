import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JobMatches } from "./JobMatches";

function job(id: string, score: number) {
  return {
    id,
    title: `Vaga ${id}`,
    company: "Stone",
    location: "São Paulo",
    url: `https://job-boards.greenhouse.io/stone/jobs/${id}`,
    score,
    reasons: ["Cargo compatível com Analista de Dados", "Pede SQL, Python"],
    matched_skills: ["SQL", "Python"],
  };
}

describe("JobMatches", () => {
  it("mostra cada vaga com empresa, motivo e link para a fonte", () => {
    render(<JobMatches result={{ state: "ok", jobs: [job("1", 80), job("2", 40)] }} />);

    const section = screen.getByRole("region", { name: "Vagas para você" });
    expect(within(section).getByText("Vaga 1")).toBeInTheDocument();
    const [first] = screen.getAllByRole("link", { name: "Ver vaga e candidatar-se" });
    expect(first).toHaveAttribute("href", "https://job-boards.greenhouse.io/stone/jobs/1");
    expect(first).toHaveAttribute("target", "_blank");
    expect(first).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getAllByText("Stone · São Paulo")).toHaveLength(2);
    expect(screen.getAllByText("Pede SQL, Python")).toHaveLength(2);
  });

  it("separa as que combinam muito das que só combinam", () => {
    render(<JobMatches result={{ state: "ok", jobs: [job("1", 80), job("2", 40)] }} />);

    expect(screen.getByText("Combina muito")).toBeInTheDocument();
    expect(screen.getByText("Combina")).toBeInTheDocument();
  });

  it("avisa quando nenhuma vaga combina", () => {
    render(<JobMatches result={{ state: "ok", jobs: [] }} />);

    expect(screen.getByText(/Nenhuma vaga combina com o seu perfil agora/)).toBeInTheDocument();
  });

  it("mostra o erro quando não consegue carregar", () => {
    render(<JobMatches result={{ state: "error", message: "Tente de novo." }} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Tente de novo.");
  });

  it("sem currículo analisado, não mostra a seção", () => {
    const { container } = render(<JobMatches result={{ state: "no-profile" }} />);

    expect(container).toBeEmptyDOMElement();
  });
});
