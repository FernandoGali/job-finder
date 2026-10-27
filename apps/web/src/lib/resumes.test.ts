import { describe, expect, it, vi } from "vitest";

import { analyzeResume, fetchResumes, fileProblem, MAX_BYTES, uploadResume } from "./resumes";

const resume = {
  id: "r-1",
  original_filename: "cv.pdf",
  content_type: "application/pdf",
  size_bytes: 1000,
  uploaded_at: "2026-10-27T18:00:00Z",
};

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status });
}

describe("fileProblem", () => {
  it("aceita PDF e DOCX de até 5 MB", () => {
    expect(fileProblem({ name: "CV.PDF", size: 1000 })).toBeNull();
    expect(fileProblem({ name: "cv.docx", size: MAX_BYTES })).toBeNull();
  });

  it("recusa outros formatos, arquivos grandes e vazios", () => {
    expect(fileProblem({ name: "cv.doc", size: 1000 })).toBe("Envie o currículo em PDF ou DOCX.");
    expect(fileProblem({ name: "cv.pdf", size: MAX_BYTES + 1 })).toBe("O arquivo passa de 5 MB.");
    expect(fileProblem({ name: "cv.pdf", size: 0 })).toBe("O arquivo está vazio.");
  });
});

describe("uploadResume", () => {
  const file = new File(["%PDF-1.7"], "cv.pdf", { type: "application/pdf" });

  it("envia o arquivo com o token e o aceite do termo", async () => {
    const fetcher = vi.fn().mockResolvedValue(json(resume, 201));

    const result = await uploadResume("token-abc", file, fetcher, "http://api.test");

    expect(result).toEqual({ state: "ok", resume });
    const [url, init] = fetcher.mock.calls[0];
    expect(url).toBe("http://api.test/curriculos");
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ Authorization: "Bearer token-abc" });
    const body = init.body as FormData;
    expect((body.get("file") as File).name).toBe("cv.pdf");
    expect(body.get("consent")).toBe("true");
    expect(body.get("consent_version")).toBe("v1");
  });

  it("mostra a mensagem da API quando ela recusa o arquivo", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ detail: "Envie o currículo em PDF ou DOCX." }, 415));

    expect(await uploadResume("t", file, fetcher, "http://api.test")).toEqual({
      state: "error",
      message: "Envie o currículo em PDF ou DOCX.",
    });
  });

  it("pede para entrar de novo quando a sessão expirou", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ detail: "qualquer" }, 401));

    const result = await uploadResume("t", file, fetcher, "http://api.test");

    expect(result).toEqual({ state: "error", message: "Sua sessão expirou. Saia e entre de novo." });
  });

  it("usa mensagem genérica quando a resposta não é JSON", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response("erro interno", { status: 500 }));

    expect(await uploadResume("t", file, fetcher, "http://api.test")).toEqual({
      state: "error",
      message: "Algo deu errado. Tente de novo.",
    });
  });

  it("avisa sem lançar erro quando a API está fora do ar", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    const result = await uploadResume("t", file, fetcher, "http://api.test");

    expect(result.state).toBe("error");
  });
});

describe("fetchResumes", () => {
  it("lista os currículos com o token", async () => {
    const fetcher = vi.fn().mockResolvedValue(json([resume]));

    expect(await fetchResumes("token-abc", fetcher, "http://api.test")).toEqual({
      state: "ok",
      resumes: [resume],
    });
    expect(fetcher).toHaveBeenCalledWith("http://api.test/curriculos", {
      cache: "no-store",
      headers: { Authorization: "Bearer token-abc" },
    });
  });

  it("devolve a mensagem de erro da API", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ detail: "Não foi possível carregar." }, 502));

    expect(await fetchResumes("t", fetcher, "http://api.test")).toEqual({
      state: "error",
      message: "Não foi possível carregar.",
    });
  });

  it("avisa sem lançar erro quando a API está fora do ar", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    expect((await fetchResumes("t", fetcher, "http://api.test")).state).toBe("error");
  });
});

describe("analyzeResume", () => {
  const profile = { target_role: "Analista de Dados", seniority: "pleno", skills: ["SQL"], certifications: [], search_terms: [], summary: "x" };

  it("pede a análise com o token e devolve o perfil", async () => {
    const fetcher = vi.fn().mockResolvedValue(json(profile));

    expect(await analyzeResume("token-abc", "r-1", fetcher, "http://api.test")).toEqual({
      state: "ok",
      profile,
    });
    expect(fetcher).toHaveBeenCalledWith("http://api.test/curriculos/r-1/analise", {
      method: "POST",
      headers: { Authorization: "Bearer token-abc" },
    });
  });

  it("devolve a mensagem da API quando a análise falha", async () => {
    const fetcher = vi.fn().mockResolvedValue(json({ detail: "Não conseguimos ler o texto." }, 422));

    expect(await analyzeResume("t", "r-1", fetcher, "http://api.test")).toEqual({
      state: "error",
      message: "Não conseguimos ler o texto.",
    });
  });

  it("avisa sem lançar erro quando a API está fora do ar", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("connection refused"));

    expect((await analyzeResume("t", "r-1", fetcher, "http://api.test")).state).toBe("error");
  });
});
