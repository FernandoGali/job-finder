import { describe, expect, it, vi } from "vitest";

import { fetchJobMatches } from "./jobs";

const job = {
  id: "a",
  title: "Analista de Dados Júnior",
  company: "Stone",
  location: "São Paulo",
  url: "https://job-boards.greenhouse.io/stone/jobs/1",
  score: 80,
  reasons: ["Pede SQL"],
  matched_skills: ["SQL"],
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

describe("fetchJobMatches", () => {
  it("busca as vagas com o token", async () => {
    const fetcher = vi.fn().mockResolvedValue(json([job]));

    expect(await fetchJobMatches("token-abc", fetcher, "http://api.test")).toEqual({ state: "ok", jobs: [job] });
    expect(fetcher).toHaveBeenCalledWith("http://api.test/vagas", {
      cache: "no-store",
      headers: { Authorization: "Bearer token-abc" },
    });
  });

  it("sem currículo analisado, avisa sem tratar como erro", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ detail: "Analise seu currículo" }, 409));

    expect(await fetchJobMatches("t", fetcher, "http://api.test")).toEqual({ state: "no-profile" });
  });

  it("devolve a mensagem da API em caso de erro", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ detail: "Não foi possível carregar as vagas agora." }, 502));

    expect(await fetchJobMatches("t", fetcher, "http://api.test")).toEqual({
      state: "error",
      message: "Não foi possível carregar as vagas agora.",
    });
  });

  it("avisa sem lançar erro quando a API está fora do ar", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    expect((await fetchJobMatches("t", fetcher, "http://api.test")).state).toBe("error");
  });
});
