import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DeleteResumeButton } from "./DeleteResumeButton";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

describe("DeleteResumeButton", () => {
  beforeEach(() => refresh.mockReset());

  it("pede confirmação, exclui e recarrega a página", async () => {
    const remove = vi.fn().mockResolvedValue({ state: "ok" });
    const confirm = vi.fn().mockReturnValue(true);
    render(<DeleteResumeButton resumeId="r-1" filename="cv.pdf" remove={remove} confirm={confirm} />);

    fireEvent.click(screen.getByRole("button", { name: "Excluir" }));

    await waitFor(() => expect(refresh).toHaveBeenCalledOnce());
    expect(confirm).toHaveBeenCalledWith('Excluir o currículo "cv.pdf"? Isso não pode ser desfeito.');
    expect(remove).toHaveBeenCalledWith("r-1");
  });

  it("não exclui se a pessoa cancelar", () => {
    const remove = vi.fn();
    render(<DeleteResumeButton resumeId="r-1" filename="cv.pdf" remove={remove} confirm={() => false} />);

    fireEvent.click(screen.getByRole("button", { name: "Excluir" }));

    expect(remove).not.toHaveBeenCalled();
  });

  it("mostra o erro quando não consegue excluir", async () => {
    const remove = vi.fn().mockResolvedValue({ state: "error", message: "Tente de novo." });
    render(<DeleteResumeButton resumeId="r-1" filename="cv.pdf" remove={remove} confirm={() => true} />);

    fireEvent.click(screen.getByRole("button", { name: "Excluir" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Tente de novo.");
    expect(refresh).not.toHaveBeenCalled();
  });
});
