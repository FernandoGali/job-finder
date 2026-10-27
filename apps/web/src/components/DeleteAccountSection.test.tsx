import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { DeleteAccountSection } from "./DeleteAccountSection";

function setup(result = { state: "ok" } as const) {
  const deleteAccount = vi.fn().mockResolvedValue(result);
  const onDeleted = vi.fn();
  render(<DeleteAccountSection deleteAccount={deleteAccount} onDeleted={onDeleted} />);
  fireEvent.click(screen.getByRole("button", { name: "Quero excluir minha conta" }));
  return { deleteAccount, onDeleted };
}

const finalButton = () => screen.getByRole("button", { name: "Excluir minha conta definitivamente" });

describe("DeleteAccountSection", () => {
  it("só libera a exclusão depois de digitar EXCLUIR", () => {
    setup();
    expect(finalButton()).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/digite EXCLUIR/), { target: { value: "excluir" } });
    expect(finalButton()).toBeDisabled();

    fireEvent.change(screen.getByLabelText(/digite EXCLUIR/), { target: { value: "EXCLUIR" } });
    expect(finalButton()).toBeEnabled();
  });

  it("exclui a conta e avisa a página", async () => {
    const { deleteAccount, onDeleted } = setup();

    fireEvent.change(screen.getByLabelText(/digite EXCLUIR/), { target: { value: "EXCLUIR" } });
    fireEvent.click(finalButton());

    await waitFor(() => expect(onDeleted).toHaveBeenCalledOnce());
    expect(deleteAccount).toHaveBeenCalledOnce();
  });

  it("mostra o erro e deixa tentar de novo", async () => {
    const { onDeleted } = setup({ state: "error", message: "Tente de novo." } as never);

    fireEvent.change(screen.getByLabelText(/digite EXCLUIR/), { target: { value: "EXCLUIR" } });
    fireEvent.click(finalButton());

    expect(await screen.findByRole("alert")).toHaveTextContent("Tente de novo.");
    expect(onDeleted).not.toHaveBeenCalled();
    expect(finalButton()).toBeEnabled();
  });

  it("permite cancelar", () => {
    setup();

    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.getByRole("button", { name: "Quero excluir minha conta" })).toBeInTheDocument();
  });
});
