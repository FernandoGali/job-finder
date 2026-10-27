import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ConfirmEmailForm } from "./ConfirmEmailForm";

describe("ConfirmEmailForm", () => {
  it("só confirma quando a pessoa clica no botão", async () => {
    const action = vi.fn();
    render(<ConfirmEmailForm params={{ tokenHash: "abc123", type: "email" }} action={action} />);

    // Abrir a página (o que o robô do e-mail faz) não confirma nada.
    expect(action).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Confirmar meu e-mail" }));

    await waitFor(() => expect(action).toHaveBeenCalledOnce());
    const formData: FormData = action.mock.calls[0][0];
    expect(formData.get("token_hash")).toBe("abc123");
    expect(formData.get("type")).toBe("email");
  });
});
