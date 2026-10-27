// Tipos de link de e-mail que esta tela aceita confirmar.
const ALLOWED_TYPES = ["email", "signup"] as const;

export type ConfirmParams = { tokenHash: string; type: (typeof ALLOWED_TYPES)[number] };

/** Lê token_hash e type do link do e-mail. Devolve null se algo estiver faltando ou estranho. */
export function parseConfirmParams(params: {
  token_hash?: unknown;
  type?: unknown;
}): ConfirmParams | null {
  const { token_hash: tokenHash, type } = params;
  if (typeof tokenHash !== "string" || tokenHash === "") {
    return null;
  }
  if (!ALLOWED_TYPES.includes(type as ConfirmParams["type"])) {
    return null;
  }
  return { tokenHash, type: type as ConfirmParams["type"] };
}
