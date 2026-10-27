import { describe, expect, it } from "vitest";

import { authErrorMessage } from "./messages";

describe("authErrorMessage", () => {
  it("traduz erros conhecidos do Supabase", () => {
    expect(authErrorMessage({ code: "invalid_credentials" })).toBe("E-mail ou senha incorretos.");
    expect(authErrorMessage({ code: "user_already_exists" })).toContain("Tente entrar");
  });

  it("usa uma mensagem genérica para erros desconhecidos ou sem código", () => {
    expect(authErrorMessage({ code: "algo_novo" })).toBe("Não foi possível concluir. Tente de novo.");
    expect(authErrorMessage({})).toBe("Não foi possível concluir. Tente de novo.");
  });
});
