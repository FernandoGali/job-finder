import { describe, expect, it, vi } from "vitest";

import { fetchApiStatus } from "./api";

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
