import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { RewriteResult } from "@/lib/resumes";

import { RewriteQuestions } from "./RewriteQuestions";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const questions = ["Quantos relatórios você automatizou?", "Quantas pessoas usavam?"];
const ok: RewriteResult = {
  state: "ok",
  rewrite: { headline: null, summary: "", experiences: [], education: [], skills: [], certifications: [], questions: [] },
};

describe("RewriteQuestions", () => {
  beforeEach(() => refresh.mockReset());

  it("manda só as perguntas respondidas e recarrega a página", async () => {
    const rewrite = vi.fn().mockResolvedValue(ok);
    render(<RewriteQuestions resumeId="r-1" questions={questions} rewrite={rewrite} />);
    const button = screen.getByRole("button", { name: "Reescrever com minhas respostas" });

    // Sem nenhuma resposta, não há o que reescrever.
    expect(button).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Quantos relatórios você automatizou?"), {
      target: { value: "  12 por semana " },
    });
    fireEvent.click(button);

    await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
    expect(rewrite).toHaveBeenCalledWith("r-1", [
      { question: "Quantos relatórios você automatizou?", answer: "12 por semana" },
    ]);
  });

  it("mostra o erro da reescrita", async () => {
    const rewrite = vi.fn().mockResolvedValue({ state: "error", message: "A reescrita está indisponível agora." });
    render(<RewriteQuestions resumeId="r-1" questions={questions} rewrite={rewrite} />);

    fireEvent.change(screen.getByLabelText("Quantas pessoas usavam?"), { target: { value: "80" } });
    fireEvent.click(screen.getByRole("button", { name: "Reescrever com minhas respostas" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("A reescrita está indisponível agora.");
    expect(refresh).not.toHaveBeenCalled();
  });
});
