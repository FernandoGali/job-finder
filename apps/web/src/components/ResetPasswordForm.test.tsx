import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { ResetPasswordForm } from "./ResetPasswordForm";

const link = { token_hash: "abc123", type: "recovery" as const };
const save = () => screen.getByRole("button", { name: "Salvar senha nova" });

function fill(password: string, confirmation: string) {
  fireEvent.change(screen.getByLabelText("Senha nova"), { target: { value: password } });
  fireEvent.change(screen.getByLabelText("Repita a senha nova"), { target: { value: confirmation } });
}

describe("ResetPasswordForm", () => {
  it("só libera com senha dentro da regra e repetida igual", () => {
    render(<ResetPasswordForm link={link} action={vi.fn()} />);
    expect(save()).toBeDisabled();

    fill("senhafraca", "senhafraca");
    expect(save()).toBeDisabled();

    fill("Senha2026", "Senha2025");
    expect(save()).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("ainda não são iguais");

    fill("Senha2026", "Senha2026");
    expect(save()).toBeEnabled();
  });

  it("envia o código do link junto com a senha nova", async () => {
    const action = vi.fn().mockResolvedValue({ error: null });
    render(<ResetPasswordForm link={link} action={action} />);

    fill("Senha2026", "Senha2026");
    fireEvent.click(save());

    await waitFor(() => expect(action).toHaveBeenCalledOnce());
    const formData: FormData = action.mock.calls[0][1];
    expect(formData.get("token_hash")).toBe("abc123");
    expect(formData.get("type")).toBe("recovery");
    expect(formData.get("password")).toBe("Senha2026");
    expect(formData.get("confirmation")).toBe("Senha2026");
  });

  it("com o link padrão do Supabase, envia o código de troca", async () => {
    const action = vi.fn().mockResolvedValue({ error: null });
    render(<ResetPasswordForm link={{ code: "codigo-pkce" }} action={action} />);

    fill("Senha2026", "Senha2026");
    fireEvent.click(save());

    await waitFor(() => expect(action).toHaveBeenCalledOnce());
    const formData: FormData = action.mock.calls[0][1];
    expect(formData.get("code")).toBe("codigo-pkce");
    expect(formData.get("token_hash")).toBeNull();
  });

  it("mostra o erro devolvido pelo servidor", async () => {
    const action = vi.fn().mockResolvedValue({ error: "A senha nova precisa ser diferente da atual." });
    render(<ResetPasswordForm link={link} action={action} />);

    fill("Senha2026", "Senha2026");
    fireEvent.click(save());

    expect(await screen.findByRole("alert")).toHaveTextContent("diferente da atual");
  });

  it("mostra a regra da senha com as bolinhas", () => {
    render(<ResetPasswordForm link={link} action={vi.fn()} />);

    expect(screen.getByRole("list", { name: "Regras da senha" })).toBeInTheDocument();
  });
});
