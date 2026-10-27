/** URL e chave pública do Supabase. Falha com uma mensagem clara se faltar no .env. */
export function supabaseEnv(): { url: string; anonKey: string } {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anonKey) {
    throw new Error("Supabase não configurado: preencha SUPABASE_URL e SUPABASE_ANON_KEY no .env");
  }
  return { url, anonKey };
}
