import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JobSearchLinks } from "./JobSearchLinks";

const linkedin = () => screen.getByRole("link", { name: "Buscar no LinkedIn" });
const SUGGESTIONS = ["Analista de Dados", "Analista de BI"];

describe("JobSearchLinks", () => {
  it("começa com a primeira sugestão e abre os sites em nova aba", () => {
    render(<JobSearchLinks suggestions={SUGGESTIONS} />);

    expect(screen.getByLabelText("O que buscar")).toHaveValue("Analista de Dados");
    expect(screen.getByRole("button", { name: "Analista de Dados" })).toHaveAttribute("aria-pressed", "true");
    expect(linkedin()).toHaveAttribute(
      "href",
      "https://www.linkedin.com/jobs/search/?keywords=%22Analista%20de%20Dados%22",
    );
    expect(linkedin()).toHaveAttribute("target", "_blank");
    expect(linkedin()).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getAllByRole("link")).toHaveLength(7);
  });

  it("um clique na sugestão troca a busca", () => {
    render(<JobSearchLinks suggestions={SUGGESTIONS} />);

    fireEvent.click(screen.getByRole("button", { name: "Analista de BI" }));

    expect(screen.getByLabelText("O que buscar")).toHaveValue("Analista de BI");
    expect(linkedin().getAttribute("href")).toContain("keywords=%22Analista%20de%20BI%22");
  });

  it("atualiza os links quando a pessoa escreve a busca, o local e marca só remotas", () => {
    render(<JobSearchLinks suggestions={SUGGESTIONS} />);

    fireEvent.change(screen.getByLabelText("O que buscar"), { target: { value: "Estágio BI" } });
    fireEvent.change(screen.getByLabelText(/Onde/), { target: { value: "Curitiba" } });
    fireEvent.click(screen.getByLabelText("Só vagas remotas (LinkedIn)"));

    expect(linkedin()).toHaveAttribute(
      "href",
      "https://www.linkedin.com/jobs/search/?keywords=%22Est%C3%A1gio%20BI%22&location=Curitiba&f_WT=2",
    );
  });

  it("o nível começa com a senioridade do perfil e pode virar qualquer nível", () => {
    render(<JobSearchLinks suggestions={SUGGESTIONS} seniority="junior" />);

    expect(screen.getByLabelText("Nível (LinkedIn e Indeed)")).toHaveValue("junior");
    expect(linkedin().getAttribute("href")).toContain("f_E=2%2C3");

    fireEvent.change(screen.getByLabelText("Nível (LinkedIn e Indeed)"), { target: { value: "" } });

    expect(linkedin().getAttribute("href")).not.toContain("f_E");
  });

  it("sem sugestões, começa vazio e pede um termo", () => {
    render(<JobSearchLinks suggestions={[]} />);

    expect(screen.queryByRole("group", { name: "Sugestões de busca" })).not.toBeInTheDocument();
    expect(screen.queryAllByRole("link")).toHaveLength(0);
    expect(screen.getByRole("status")).toHaveTextContent("Escreva o que buscar");
  });
});
