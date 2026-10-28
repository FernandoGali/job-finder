import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ForgotPasswordForm } from "./ForgotPasswordForm";

function submit(email = "ana@exemplo.com") {
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: email } });
  fireEvent.click(screen.getByRole("button", { name: "Enviar link" }));
}

describe("ForgotPasswordForm", () => {
  it("envia o link e mostra a mesma mensagem exista a conta ou não", async () => {
    const send = vi.fn().mockResolvedValue({ error: null });
    render(<ForgotPasswordForm send={send} />);

    submit();

    expect(await screen.findByRole("status")).toHaveTextContent("Se houver uma conta com esse e-mail");
    expect(send).toHaveBeenCalledWith("ana@exemplo.com");
  });

  it("não revela erros que dariam pistas sobre a conta", async () => {
    const send = vi.fn().mockResolvedValue({ error: { code: "user_not_found" } });
    render(<ForgotPasswordForm send={send} />);

    submit();

    expect(await screen.findByRole("status")).toHaveTextContent("Se houver uma conta com esse e-mail");
  });

  it("avisa quando passou do limite de e-mails", async () => {
    const send = vi.fn().mockResolvedValue({ error: { code: "over_email_send_rate_limit" } });
    render(<ForgotPasswordForm send={send} />);

    submit();

    expect(await screen.findByRole("alert")).toHaveTextContent("Muitos e-mails enviados");
  });

  it("mostra o aviso de link inválido vindo da página", async () => {
    render(<ForgotPasswordForm send={vi.fn()} notice="O link não funcionou." />);

    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("O link não funcionou."));
  });
});
