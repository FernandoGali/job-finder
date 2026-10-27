import { describe, expect, it } from "vitest";

import { parseConfirmParams } from "./confirm";

describe("parseConfirmParams", () => {
  it("aceita o link de confirmação de cadastro", () => {
    expect(parseConfirmParams({ token_hash: "abc123", type: "email" })).toEqual({
      tokenHash: "abc123",
      type: "email",
    });
    expect(parseConfirmParams({ token_hash: "abc123", type: "signup" })?.type).toBe("signup");
  });

  it("recusa link sem token", () => {
    expect(parseConfirmParams({ type: "email" })).toBeNull();
    expect(parseConfirmParams({ token_hash: "", type: "email" })).toBeNull();
  });

  it("recusa tipos que esta tela não trata", () => {
    expect(parseConfirmParams({ token_hash: "abc123", type: "recovery" })).toBeNull();
    expect(parseConfirmParams({ token_hash: "abc123" })).toBeNull();
  });

  it("recusa parâmetros repetidos na URL", () => {
    expect(parseConfirmParams({ token_hash: ["a", "b"], type: "email" })).toBeNull();
  });
});
