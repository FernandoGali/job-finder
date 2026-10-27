import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JobSearchLinks } from "./JobSearchLinks";

const linkedin = () => screen.getByRole("link", { name: "Buscar no LinkedIn" });

describe("JobSearchLinks", () => {
  it("começa com o cargo-alvo do perfil e abre os sites em nova aba", () => {
    render(<JobSearchLinks initialQuery="Analista de Dados" />);

    expect(screen.getByLabelText("O que buscar")).toHaveValue("Analista de Dados");
    expect(linkedin()).toHaveAttribute(
      "href",
      "https://www.linkedin.com/jobs/search/?keywords=Analista%20de%20Dados",
    );
    expect(linkedin()).toHaveAttribute("target", "_blank");
    expect(linkedin()).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getAllByRole("link")).toHaveLength(7);
  });

  it("atualiza os links quando a pessoa muda a busca e o local", () => {
    render(<JobSearchLinks initialQuery="Analista de Dados" />);

    fireEvent.change(screen.getByLabelText("O que buscar"), { target: { value: "Estágio BI" } });
    fireEvent.change(screen.getByLabelText(/Onde/), { target: { value: "Curitiba" } });

    expect(linkedin()).toHaveAttribute(
      "href",
      "https://www.linkedin.com/jobs/search/?keywords=Est%C3%A1gio%20BI&location=Curitiba",
    );
  });

  it("pede um termo quando a busca fica vazia", () => {
    render(<JobSearchLinks initialQuery="Analista de Dados" />);

    fireEvent.change(screen.getByLabelText("O que buscar"), { target: { value: "" } });

    expect(screen.queryAllByRole("link")).toHaveLength(0);
    expect(screen.getByRole("status")).toHaveTextContent("Escreva o que buscar");
  });
});
