// Tipos de link de e-mail que cada tela aceita.
export const SIGNUP_TYPES = ["email", "signup"] as const;
export const RECOVERY_TYPES = ["recovery"] as const;

type LinkType = (typeof SIGNUP_TYPES)[number] | (typeof RECOVERY_TYPES)[number];

export type ConfirmParams = { tokenHash: string; type: LinkType };

/**
 * Link de redefinição de senha. Formato do nosso modelo de e-mail (token_hash) ou, se o
 * modelo padrão do Supabase estiver ativo, o código de troca (code), que só funciona no mesmo
 * navegador que pediu o link.
 */
export type RecoveryLink = { token_hash: string; type: "recovery" } | { code: string };

export function parseRecoveryLink(params: {
  token_hash?: unknown;
  type?: unknown;
  code?: unknown;
}): RecoveryLink | null {
  const confirm = parseConfirmParams(params, RECOVERY_TYPES);
  if (confirm) {
    return { token_hash: confirm.tokenHash, type: "recovery" };
  }
  if (typeof params.code === "string" && params.code !== "") {
    return { code: params.code };
  }
  return null;
}

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
