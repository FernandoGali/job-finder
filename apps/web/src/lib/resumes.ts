import { apiBaseUrl } from "./api";

// Precisa ser igual ao CONSENT_VERSION da API (apps/api/.../resumes.py).
export const CONSENT_VERSION = "v1";
export const CONSENT_TEXT =
  "Autorizo o Job Finder a guardar meu currículo e analisá-lo com inteligência artificial " +
  "para encontrar vagas compatíveis com o meu perfil. Sei que posso excluir meu currículo " +
  "e minha conta quando quiser.";

export const MAX_BYTES = 5 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = [".pdf", ".docx"];
export const ACCEPT_ATTRIBUTE = ACCEPTED_EXTENSIONS.join(",");

export type Resume = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  uploaded_at: string;
};

export type UploadResult = { state: "ok"; resume: Resume } | { state: "error"; message: string };

export type ResumesResult = { state: "ok"; resumes: Resume[] } | { state: "error"; message: string };

const SESSION_EXPIRED = "Sua sessão expirou. Saia e entre de novo.";
const API_OFFLINE = "Não foi possível falar com o servidor. Tente de novo em instantes.";

/** Avisa antes de enviar. A API confere de novo (inclusive o conteúdo do arquivo). */
export function fileProblem(file: { name: string; size: number }): string | null {
  const name = file.name.toLowerCase();
  if (!ACCEPTED_EXTENSIONS.some((extension) => name.endsWith(extension))) {
    return "Envie o currículo em PDF ou DOCX.";
  }
  if (file.size > MAX_BYTES) {
    return "O arquivo passa de 5 MB.";
  }
  if (file.size === 0) {
    return "O arquivo está vazio.";
  }
  return null;
}

export async function uploadResume(
  accessToken: string,
  file: File,
  fetcher: typeof fetch = fetch,
  baseUrl: string = apiBaseUrl(),
): Promise<UploadResult> {
  const body = new FormData();
  body.append("file", file);
  body.append("consent", "true");
  body.append("consent_version", CONSENT_VERSION);

  try {
    const response = await fetcher(`${baseUrl}/curriculos`, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body,
    });
    if (response.ok) {
      return { state: "ok", resume: (await response.json()) as Resume };
    }
    return { state: "error", message: await errorMessage(response) };
  } catch {
    return { state: "error", message: API_OFFLINE };
  }
}

export async function fetchResumes(
  accessToken: string,
  fetcher: typeof fetch = fetch,
  baseUrl: string = apiBaseUrl(),
): Promise<ResumesResult> {
  try {
    const response = await fetcher(`${baseUrl}/curriculos`, {
      cache: "no-store",
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (response.ok) {
      return { state: "ok", resumes: (await response.json()) as Resume[] };
    }
    return { state: "error", message: await errorMessage(response) };
  } catch {
    return { state: "error", message: API_OFFLINE };
  }
}

/** As mensagens da API já vêm em português; 401 vira um pedido para entrar de novo. */
async function errorMessage(response: Response): Promise<string> {
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
