import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";

import { supabaseEnv } from "./env";

/** Cliente do Supabase para páginas e rotas do servidor. Criar um por requisição. */
export async function createClient() {
  // cookies() primeiro: ele marca a página como dinâmica, então o build não tenta
  // montá-la sem .env (como no CI).
  const cookieStore = await cookies();
  const { url, anonKey } = supabaseEnv();

  return createServerClient(url, anonKey, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options);
          }
        } catch {
          // Páginas do servidor não podem gravar cookies; o middleware renova a sessão.
        }
      },
    },
  });
}
