import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { JobDemand } from "./JobDemand";

describe("JobDemand", () => {
  it("mostra, por cargo, a porcentagem das vagas e se o currículo cita cada item", () => {
    render(
      <JobDemand
        result={{
          state: "ok",
          roles: [
            {
              role: "Analista de Dados",
              jobs: 12,
              items: [
                { name: "SQL", jobs: 12, share: 100, in_resume: true },
                { name: "Estatística", jobs: 7, share: 58, in_resume: false },
              ],
            },
            { role: "Analista de Melhoria Contínua", jobs: 1, items: [] },
          ],
        }}
      />,
    );

    const section = screen.getByRole("region", { name: "O que as vagas pedem" });
    expect(section).toHaveTextContent("Analista de Dados · 12 vagas");
    const items = within(screen.getByRole("list", { name: "Mais pedidos para Analista de Dados" })).getAllByRole(
      "listitem",
    );
    expect(items[0]).toHaveTextContent("SQL100% das vagas✓ No seu currículo");
    expect(items[1]).toHaveTextContent("Estatística58% das vagasNão está no currículo");
    // Com poucas vagas, não mostra porcentagem nenhuma.
    expect(section).toHaveTextContent("Analista de Melhoria Contínua · 1 vaga");
    expect(section).toHaveTextContent("Poucas vagas desse cargo");
  });

  it("mostra o erro da API", () => {
    render(<JobDemand result={{ state: "error", message: "Não foi possível carregar as vagas agora." }} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Não foi possível carregar as vagas agora.");
  });

  it("some sem currículo analisado ou sem cargos", () => {
    const { container, rerender } = render(<JobDemand result={{ state: "no-profile" }} />);
    expect(container).toBeEmptyDOMElement();

    rerender(<JobDemand result={{ state: "ok", roles: [] }} />);
    expect(container).toBeEmptyDOMElement();
  });
});
