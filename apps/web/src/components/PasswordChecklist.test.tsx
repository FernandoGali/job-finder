import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PasswordChecklist } from "./PasswordChecklist";

function checks() {
  return screen
    .getAllByRole("listitem")
    .map((item) => [item.textContent?.replace(/\(ok\)|\(falta\)/, ""), item.dataset.ok]);
}

describe("PasswordChecklist", () => {
  it("começa com todas as regras pendentes", () => {
    render(<PasswordChecklist password="" />);

    expect(checks()).toEqual([
      ["Mínimo de 8 caracteres;", "false"],
      ["Mínimo de 1 letra minúscula;", "false"],
      ["Mínimo de 1 letra maiúscula;", "false"],
      ["Mínimo de 1 número.", "false"],
    ]);
  });

  it("marca só as regras que a senha já cumpre", () => {
    render(<PasswordChecklist password="abcD" />);

    expect(checks().map(([, ok]) => ok)).toEqual(["false", "true", "true", "false"]);
  });

  it("marca tudo quando a senha cumpre a regra inteira", () => {
    render(<PasswordChecklist password="Senha2026" />);

    expect(checks().every(([, ok]) => ok === "true")).toBe(true);
    expect(screen.getAllByText("(ok)")).toHaveLength(4);
  });
});
