import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { RewriteResult } from "@/lib/resumes";

import { RewriteButton } from "./RewriteButton";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const rewrite = {
  headline: null,
  summary: "",
  experiences: [],
  education: [],
  skills: [],
  certifications: [],
  questions: [],
};

describe("RewriteButton", () => {
  beforeEach(() => refresh.mockReset());

  it("pede a reescrita, avisa que pode demorar e recarrega a página", async () => {
    let finish: (value: RewriteResult) => void = () => {};
    const run = vi.fn(() => new Promise<RewriteResult>((r) => (finish = r)));
    render(<RewriteButton resumeId="r-1" label="Reescrever para ATS" rewrite={run} />);

    fireEvent.click(screen.getByRole("button", { name: "Reescrever para ATS" }));

    expect(await screen.findByRole("button", { name: /Reescrevendo/ })).toBeDisabled();
    finish({ state: "ok", rewrite });
    await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
    expect(run).toHaveBeenCalledWith("r-1");
  });

  it("mostra o erro da reescrita", async () => {
    const run = vi.fn().mockResolvedValue({ state: "error", message: "Analise o currículo antes de reescrever." });
    render(<RewriteButton resumeId="r-1" label="Reescrever para ATS" rewrite={run} />);

    fireEvent.click(screen.getByRole("button", { name: "Reescrever para ATS" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Analise o currículo antes de reescrever.");
    expect(refresh).not.toHaveBeenCalled();
  });
});
