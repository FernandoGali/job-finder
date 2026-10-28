import { API_OFFLINE, apiBaseUrl, apiErrorMessage } from "./api";

export type JobMatch = {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  score: number;
  reasons: string[];
  matched_skills: string[];
};

export type JobMatchesResult =
  | { state: "ok"; jobs: JobMatch[] }
  | { state: "no-profile" }
  | { state: "error"; message: string };

/** Vagas recomendadas para o perfil do currículo analisado mais recente. Nunca lança erro. */
export async function fetchJobMatches(
  accessToken: string,
  fetcher: typeof fetch = fetch,
  baseUrl: string = apiBaseUrl(),
): Promise<JobMatchesResult> {
  try {
    const response = await fetcher(`${baseUrl}/vagas`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (response.ok) {
      return { state: "ok", jobs: (await response.json()) as JobMatch[] };
    }
    if (response.status === 409) {
      return { state: "no-profile" };
    }
    return { state: "error", message: await apiErrorMessage(response) };
  } catch {
    return { state: "error", message: API_OFFLINE };
  }
}
