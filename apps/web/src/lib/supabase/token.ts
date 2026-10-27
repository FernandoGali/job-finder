import { createClient } from "./client";

/** Token da sessão atual no navegador, para enviar à API. null se a sessão acabou. */
export async function getAccessToken(): Promise<string | null> {
  const { data } = await createClient().auth.getSession();
  return data.session?.access_token ?? null;
}
