import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { formatSize, ResumeList } from "./ResumeList";

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));

function resume(id: string, name: string, uploadedAt: string) {
  return {
    id,
    original_filename: name,
    content_type: "application/pdf",
    size_bytes: 250 * 1024,
    uploaded_at: uploadedAt,
  };
}

describe("ResumeList", () => {
  it("mostra o currículo mais recente com tamanho e data no horário de Brasília", () => {
    render(
      <ResumeList
        result={{ state: "ok", resumes: [resume("2", "novo.pdf", "2026-10-27T18:30:00Z")] }}
      />,
    );

    const section = screen.getByRole("region", { name: "Meus currículos" });
    expect(section).toHaveTextContent("novo.pdf · 250 KB · enviado em 27/10/2026, 15:30");
  });

  it("guarda os envios anteriores num bloco recolhido", () => {
    render(
      <ResumeList
        result={{
          state: "ok",
          resumes: [
            resume("2", "novo.pdf", "2026-10-27T18:30:00Z"),
            resume("1", "antigo.pdf", "2026-10-20T12:00:00Z"),
          ],
        }}
      />,
    );

    expect(screen.getByText("Envios anteriores (1)")).toBeInTheDocument();
    expect(screen.getByText(/antigo\.pdf/)).toBeInTheDocument();
  });

  it("avisa quando ainda não há currículo", () => {
    render(<ResumeList result={{ state: "ok", resumes: [] }} />);

    expect(screen.getByText("Você ainda não enviou nenhum currículo.")).toBeInTheDocument();
  });

  it("mostra o erro quando não consegue carregar", () => {
    render(<ResumeList result={{ state: "error", message: "Servidor fora do ar." }} />);

    expect(screen.getByRole("alert")).toHaveTextContent("Servidor fora do ar.");
  });
});

describe("formatSize", () => {
  it("mostra KB abaixo de 1 MB e MB com vírgula acima", () => {
    expect(formatSize(100)).toBe("1 KB");
    expect(formatSize(512 * 1024)).toBe("512 KB");
    expect(formatSize(2.5 * 1024 * 1024)).toBe("2,5 MB");
  });
});

describe("ResumeList com análise", () => {
  it("mostra o perfil do currículo mais recente quando já foi analisado", () => {
    const analyzed = {
      ...resume("2", "novo.pdf", "2026-10-27T18:30:00Z"),
      profile: {
        target_role: "Analista de Dados",
        seniority: "pleno" as const,
        skills: ["SQL"],
        certifications: [],
        search_terms: ["Analista de Dados"],
        summary: "",
        analyzed_at: "2026-10-27T18:31:00Z",
      },
    };
    render(<ResumeList result={{ state: "ok", resumes: [analyzed] }} />);

    expect(screen.getByRole("region", { name: "Perfil lido pela IA" })).toHaveTextContent("Analista de Dados");
    expect(screen.getByRole("button", { name: "Analisar de novo" })).toBeInTheDocument();
  });

  it("oferece a análise quando o currículo ainda não foi analisado", () => {
    render(<ResumeList result={{ state: "ok", resumes: [resume("2", "novo.pdf", "2026-10-27T18:30:00Z")] }} />);

    expect(screen.getByText("Este currículo ainda não foi analisado.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analisar" })).toBeInTheDocument();
  });
});
