import { afterEach, describe, expect, it, vi } from "vitest";

import { supabaseEnv } from "./env";

describe("supabaseEnv", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("devolve a URL e a chave pública", () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "https://exemplo.supabase.co");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "sb_publishable_teste");

    expect(supabaseEnv()).toEqual({
      url: "https://exemplo.supabase.co",
      anonKey: "sb_publishable_teste",
    });
  });

  it("explica o que falta quando o .env não foi preenchido", () => {
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_URL", "");
    vi.stubEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "");

    expect(() => supabaseEnv()).toThrow("preencha SUPABASE_URL e SUPABASE_ANON_KEY");
  });
});
