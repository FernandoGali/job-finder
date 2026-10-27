import { describe, expect, it, vi } from "vitest";

import { callApi, fetchApiStatus } from "./api";

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

describe("callApi", () => {
  it("chama a rota com o método e o token", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));

    expect(await callApi("DELETE", "/conta", "token-abc", fetcher, "http://api.test")).toEqual({
      state: "ok",
    });
    expect(fetcher).toHaveBeenCalledWith("http://api.test/conta", {
      method: "DELETE",
      headers: { Authorization: "Bearer token-abc" },
    });
  });

  it("devolve a mensagem da API em caso de erro", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(new Response(JSON.stringify({ detail: "Currículo não encontrado." }), { status: 404 }));

    expect(await callApi("DELETE", "/curriculos/x", "t", fetcher, "http://api.test")).toEqual({
      state: "error",
      message: "Currículo não encontrado.",
    });
  });

  it("avisa sem lançar erro quando a API está fora do ar", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    expect((await callApi("DELETE", "/conta", "t", fetcher, "http://api.test")).state).toBe("error");
  });
});
