import { fileURLToPath } from "node:url";

import nextEnv from "@next/env";

// O .env fica na raiz do monorepo, não em apps/web. O Next já leu o .env de
// apps/web antes deste arquivo e guardou o resultado; forceReload lê o da raiz.
const rootDir = fileURLToPath(new URL("../..", import.meta.url));
nextEnv.loadEnvConfig(rootDir, process.env.NODE_ENV !== "production", undefined, true);

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Só a URL e a chave pública vão para o navegador. A chave secreta nunca.
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.SUPABASE_URL ?? "",
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.SUPABASE_ANON_KEY ?? "",
  },
};

export default nextConfig;
