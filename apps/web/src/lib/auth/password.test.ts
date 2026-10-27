import { describe, expect, it } from "vitest";

import { passwordProblem } from "./password";

describe("passwordProblem", () => {
  it("aceita senha com 8 ou mais caracteres, minúscula, maiúscula e número", () => {
    expect(passwordProblem("Senha123")).toBeNull();
    expect(passwordProblem("Coração 2026!")).toBeNull();
  });

  it("recusa senha curta", () => {
    expect(passwordProblem("Abc123")).toContain("pelo menos 8 caracteres");
  });

  it("recusa senha sem letra minúscula", () => {
    expect(passwordProblem("SENHA1234")).toContain("minúscula");
  });

  it("recusa senha sem letra maiúscula", () => {
    expect(passwordProblem("senha1234")).toContain("maiúscula");
  });

  it("recusa senha sem número", () => {
    expect(passwordProblem("SomenteLetras")).toContain("um número");
  });

  it("não conta letras acentuadas, como o Supabase", () => {
    expect(passwordProblem("ÇÃÉ1234abc")).toContain("maiúscula");
  });
});
