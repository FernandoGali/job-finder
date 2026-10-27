import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AnalyzeButton } from "./AnalyzeButton";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const profile = { target_role: "Dev", seniority: "pleno" as const, skills: [], summary: "" };

describe("AnalyzeButton", () => {
  beforeEach(() => refresh.mockReset());

  it("pede a análise, avisa que pode demorar e recarrega a página", async () => {
    let finish: (value: { state: "ok"; profile: typeof profile }) => void = () => {};
    const analyze = vi.fn(() => new Promise<{ state: "ok"; profile: typeof profile }>((r) => (finish = r)));
    render(<AnalyzeButton resumeId="r-1" label="Analisar com IA" analyze={analyze} />);

    fireEvent.click(screen.getByRole("button", { name: "Analisar com IA" }));

    expect(await screen.findByRole("button", { name: /Analisando/ })).toBeDisabled();
    finish({ state: "ok", profile });
    await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
    expect(analyze).toHaveBeenCalledWith("r-1");
  });

  it("mostra o erro da análise", async () => {
    const analyze = vi.fn().mockResolvedValue({ state: "error", message: "Não conseguimos ler o texto." });
    render(<AnalyzeButton resumeId="r-1" label="Analisar com IA" analyze={analyze} />);

    fireEvent.click(screen.getByRole("button", { name: "Analisar com IA" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Não conseguimos ler o texto.");
    expect(refresh).not.toHaveBeenCalled();
  });
});
