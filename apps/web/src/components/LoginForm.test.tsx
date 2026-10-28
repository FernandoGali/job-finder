import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { type AuthActions, LoginForm } from "./LoginForm";

function setup(overrides: Partial<AuthActions> = {}) {
  const auth: AuthActions = {
    signIn: vi.fn().mockResolvedValue({ error: null }),
    signUp: vi.fn().mockResolvedValue({ error: null }),
    ...overrides,
  };
  const onSignedIn = vi.fn();
  render(<LoginForm auth={auth} onSignedIn={onSignedIn} />);
  return { auth, onSignedIn };
}

function fillAndSubmit(button: string) {
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "ana@exemplo.com" } });
  fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "Senha-forte-123" } });
  fireEvent.click(screen.getByRole("button", { name: button }));
}

describe("LoginForm", () => {
  it("entra com e-mail e senha e avisa a página", async () => {
    const { auth, onSignedIn } = setup();

    fillAndSubmit("Entrar");

    await waitFor(() => expect(onSignedIn).toHaveBeenCalledOnce());
    expect(auth.signIn).toHaveBeenCalledWith("ana@exemplo.com", "Senha-forte-123");
    expect(auth.signUp).not.toHaveBeenCalled();
  });

  it("mostra o erro em português quando a senha está errada", async () => {
    const { onSignedIn } = setup({
      signIn: vi.fn().mockResolvedValue({ error: { code: "invalid_credentials" } }),
    });

    fillAndSubmit("Entrar");

    expect(await screen.findByRole("alert")).toHaveTextContent("E-mail ou senha incorretos.");
    expect(onSignedIn).not.toHaveBeenCalled();
  });

  it("cria conta e pede para confirmar o e-mail", async () => {
    const { auth, onSignedIn } = setup();

    fireEvent.click(screen.getByRole("button", { name: /Criar conta/ }));
    fillAndSubmit("Criar conta");

    expect(await screen.findByRole("status")).toHaveTextContent("link de confirmação");
    expect(auth.signUp).toHaveBeenCalledWith("ana@exemplo.com", "Senha-forte-123");
    expect(onSignedIn).not.toHaveBeenCalled();
  });

  it("no cadastro, mostra a regra e recusa senha sem número antes de enviar", async () => {
    const { auth } = setup();

    fireEvent.click(screen.getByRole("button", { name: /Criar conta/ }));
    expect(screen.getByRole("list", { name: "Regras da senha" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "ana@exemplo.com" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "SomenteLetras" } });
    fireEvent.click(screen.getByRole("button", { name: "Criar conta" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("pelo menos um número");
    expect(auth.signUp).not.toHaveBeenCalled();
  });

  it("marca as regras da senha enquanto a pessoa digita", () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: /Criar conta/ }));

    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "Senha2026" } });

    const items = screen.getAllByRole("listitem");
    expect(items.every((item) => item.dataset.ok === "true")).toBe(true);
  });

  it("no login, não aplica a regra de senha (contas antigas continuam entrando)", async () => {
    const { auth } = setup();

    fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "ana@exemplo.com" } });
    fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "somenteletras" } });
    fireEvent.click(screen.getByRole("button", { name: "Entrar" }));

    await waitFor(() => expect(auth.signIn).toHaveBeenCalledOnce());
  });

  it("mostra o aviso recebido da página, como o de link de confirmação inválido", () => {
    render(<LoginForm auth={{ signIn: vi.fn(), signUp: vi.fn() }} onSignedIn={vi.fn()} notice="Link usado" />);

    expect(screen.getByRole("status")).toHaveTextContent("Link usado");
  });

  it("no login, oferece o link de esqueci minha senha", () => {
    setup();

    expect(screen.getByRole("link", { name: "Esqueci minha senha" })).toHaveAttribute("href", "/esqueci-senha");

    fireEvent.click(screen.getByRole("button", { name: /Criar conta/ }));
    expect(screen.queryByRole("link", { name: "Esqueci minha senha" })).not.toBeInTheDocument();
  });

  it("exige senha de pelo menos 8 caracteres", () => {
    setup();

    expect(screen.getByLabelText("Senha")).toHaveAttribute("minLength", "8");
  });
});
