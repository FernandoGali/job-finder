export type Health = {
  status: string;
  version: string;
  env: string;
  supabase_configured: boolean;
};

export type ApiStatus =
  | { state: "online"; health: Health }
  | { state: "offline"; reason: string };

export type Me = { id: string; email: string | null };

export type MeResult =
  | { state: "ok"; me: Me }
  | { state: "unauthorized" }
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
    return { state: "offline", reason: errorReason(error) };
  }
}

/** Pergunta à API quem está logado, enviando o token do Supabase. Nunca lança erro. */
export async function fetchMe(
  accessToken: string,
  fetcher: typeof fetch = fetch,
  baseUrl: string = apiBaseUrl(),
): Promise<MeResult> {
  try {
    const response = await fetcher(`${baseUrl}/me`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (response.status === 401) {
      return { state: "unauthorized" };
    }
    if (!response.ok) {
      return { state: "offline", reason: `HTTP ${response.status}` };
    }
    return { state: "ok", me: (await response.json()) as Me };
  } catch (error) {
    return { state: "offline", reason: errorReason(error) };
  }
}

function errorReason(error: unknown): string {
  return error instanceof Error ? error.message : "erro desconhecido";
}
