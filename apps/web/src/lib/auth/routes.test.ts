import { describe, expect, it } from "vitest";

import { authRedirect } from "./routes";

describe("authRedirect", () => {
  it("manda para o login quem tenta abrir a área logada sem estar logado", () => {
    expect(authRedirect("/minha-area", false)).toBe("/entrar");
    expect(authRedirect("/minha-area/curriculo", false)).toBe("/entrar");
  });

  it("deixa quem está logado entrar na área logada", () => {
    expect(authRedirect("/minha-area", true)).toBeNull();
  });

  it("manda quem já está logado direto para a área logada ao abrir o login", () => {
    expect(authRedirect("/entrar", true)).toBe("/minha-area");
  });

  it("não mexe em páginas públicas", () => {
    expect(authRedirect("/", false)).toBeNull();
    expect(authRedirect("/entrar", false)).toBeNull();
    expect(authRedirect("/minha-areax", false)).toBeNull();
  });
});
