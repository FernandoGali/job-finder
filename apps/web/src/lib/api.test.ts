import { describe, expect, it, vi } from "vitest";

import { fetchApiStatus, fetchMe } from "./api";

const health = { status: "ok", version: "0.1.0", env: "development", supabase_configured: false };

describe("fetchApiStatus", () => {
  it("retorna online com os dados do /health", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(health), { status: 200 }));

    const result = await fetchApiStatus(fetcher, "http://api.test");

    expect(fetcher).toHaveBeenCalledWith("http://api.test/health", { cache: "no-store" });
    expect(result).toEqual({ state: "online", health });
  });

  it("retorna offline quando a API responde com erro", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response("falhou", { status: 503 }));

    expect(await fetchApiStatus(fetcher, "http://api.test")).toEqual({
      state: "offline",
      reason: "HTTP 503",
    });
  });

  it("retorna offline sem lançar erro quando a rede falha", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    expect(await fetchApiStatus(fetcher, "http://api.test")).toEqual({
      state: "offline",
      reason: "connection refused",
    });
  });
});

describe("fetchMe", () => {
  const me = { id: "8f0e6c3a", email: "ana@exemplo.com" };

  it("envia o token do Supabase e devolve quem está logado", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify(me), { status: 200 }));

    const result = await fetchMe("token-abc", fetcher, "http://api.test");

    expect(fetcher).toHaveBeenCalledWith("http://api.test/me", {
      cache: "no-store",
      headers: { Authorization: "Bearer token-abc" },
    });
    expect(result).toEqual({ state: "ok", me });
  });

  it("avisa quando a API não reconhece o token", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response("{}", { status: 401 }));

    expect(await fetchMe("token-velho", fetcher, "http://api.test")).toEqual({
      state: "unauthorized",
    });
  });

  it("retorna offline sem lançar erro quando a API está fora do ar", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    expect(await fetchMe("token-abc", fetcher, "http://api.test")).toEqual({
      state: "offline",
      reason: "connection refused",
    });
  });
});
