import { createBrowserClient } from "@supabase/ssr";

import { supabaseEnv } from "./env";

/** Cliente do Supabase para componentes que rodam no navegador. */
export function createClient() {
  const { url, anonKey } = supabaseEnv();
  return createBrowserClient(url, anonKey);
}
