export type Health = {
  status: string;
  version: string;
  env: string;
  supabase_configured: boolean;
};

export type ApiStatus =
  | { state: "online"; health: Health }
  | { state: "offline"; reason: string };

export function apiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
}

/** Consulta /health da API. Nunca lança erro: devolve "offline" com o motivo. */
export async function fetchApiStatus(
  fetcher: typeof fetch = fetch,
  baseUrl: string = apiBaseUrl(),
): Promise<ApiStatus> {
  try {
    const response = await fetcher(`${baseUrl}/health`, { cache: "no-store" });
    if (!response.ok) {
      return { state: "offline", reason: `HTTP ${response.status}` };
    }
    const health = (await response.json()) as Health;
    return { state: "online", health };
  } catch (error) {
    const reason = error instanceof Error ? error.message : "erro desconhecido";
    return { state: "offline", reason };
  }
}

export type ActionResult = { state: "ok" } | { state: "error"; message: string };

export const SESSION_EXPIRED = "Sua sessão expirou. Saia e entre de novo.";
export const API_OFFLINE = "Não foi possível falar com o servidor. Tente de novo em instantes.";

/** As mensagens da API já vêm em português; 401 vira um pedido para entrar de novo. */
export async function apiErrorMessage(response: Response): Promise<string> {
  if (response.status === 401) {
    return SESSION_EXPIRED;
  }
  try {
    const { detail } = (await response.json()) as { detail?: unknown };
    if (typeof detail === "string") {
      return detail;
    }
  } catch {
    // resposta sem JSON: cai na mensagem genérica
  }
  return "Algo deu errado. Tente de novo.";
}

/** Chama uma rota da API que não devolve conteúdo (ex.: DELETE). Nunca lança erro. */
export async function callApi(
  method: string,
  path: string,
  accessToken: string,
  fetcher: typeof fetch = fetch,
  baseUrl: string = apiBaseUrl(),
): Promise<ActionResult> {
  try {
    const response = await fetcher(`${baseUrl}${path}`, {
      method,
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return response.ok ? { state: "ok" } : { state: "error", message: await apiErrorMessage(response) };
  } catch {
    return { state: "error", message: API_OFFLINE };
  }
}
