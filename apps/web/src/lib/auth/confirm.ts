// Tipos de link de e-mail que cada tela aceita.
export const SIGNUP_TYPES = ["email", "signup"] as const;
export const RECOVERY_TYPES = ["recovery"] as const;

type LinkType = (typeof SIGNUP_TYPES)[number] | (typeof RECOVERY_TYPES)[number];

export type ConfirmParams = { tokenHash: string; type: LinkType };

/** Lê token_hash e type do link do e-mail. Devolve null se algo estiver faltando ou estranho. */
export function parseConfirmParams(
  params: { token_hash?: unknown; type?: unknown },
  allowed: readonly LinkType[] = SIGNUP_TYPES,
): ConfirmParams | null {
  const { token_hash: tokenHash, type } = params;
  if (typeof tokenHash !== "string" || tokenHash === "") {
    return null;
  }
  if (!allowed.includes(type as LinkType)) {
    return null;
  }
  return { tokenHash, type: type as LinkType };
}
