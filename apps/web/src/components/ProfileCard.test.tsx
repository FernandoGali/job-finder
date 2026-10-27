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
  });

  it("diz quando a IA não identificou algo, em vez de inventar", () => {
    render(<ProfileCard profile={{ target_role: null, seniority: null, skills: [], summary: "" }} />);

    const card = screen.getByRole("region", { name: "Perfil lido pela IA" });
    expect(card).toHaveTextContent("Não identificado no currículo");
    expect(card).toHaveTextContent("Não deu para deduzir");
    expect(card).toHaveTextContent("Nenhuma competência identificada.");
  });
});
