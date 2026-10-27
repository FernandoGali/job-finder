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
