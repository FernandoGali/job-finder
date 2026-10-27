"use client";

import { type FormEvent, useState } from "react";

import { authErrorMessage } from "@/lib/auth/messages";

type AuthResult = { error: { code?: string } | null };

export type AuthActions = {
  signIn: (email: string, password: string) => Promise<AuthResult>;
  signUp: (email: string, password: string) => Promise<AuthResult>;
};

type Feedback = { kind: "error" | "info"; text: string };

export function LoginForm({ auth, onSignedIn }: { auth: AuthActions; onSignedIn: () => void }) {
  const [mode, setMode] = useState<"entrar" | "cadastrar">("entrar");
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    const password = String(form.get("password"));

    setBusy(true);
    setFeedback(null);
    const { error } =
      mode === "entrar" ? await auth.signIn(email, password) : await auth.signUp(email, password);
    setBusy(false);

    if (error) {
      setFeedback({ kind: "error", text: authErrorMessage(error) });
    } else if (mode === "entrar") {
      onSignedIn();
    } else {
      setFeedback({
        kind: "info",
        text: "Conta criada! Enviamos um link de confirmação para o seu e-mail.",
      });
    }
  }

  const isLogin = mode === "entrar";
  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 360 }}>
      <h1>{isLogin ? "Entrar" : "Criar conta"}</h1>
      <label>
        E-mail
        <input name="email" type="email" autoComplete="email" required style={{ width: "100%" }} />
      </label>
      <label>
        Senha
        <input
          name="password"
          type="password"
          autoComplete={isLogin ? "current-password" : "new-password"}
          minLength={8}
          required
          style={{ width: "100%" }}
        />
      </label>
      <button type="submit" disabled={busy}>
        {busy ? "Aguarde…" : isLogin ? "Entrar" : "Criar conta"}
      </button>
      {feedback && (
        <p role={feedback.kind === "error" ? "alert" : "status"}>{feedback.text}</p>
      )}
      <button
        type="button"
        onClick={() => {
          setMode(isLogin ? "cadastrar" : "entrar");
          setFeedback(null);
        }}
      >
        {isLogin ? "Ainda não tem conta? Criar conta" : "Já tem conta? Entrar"}
      </button>
    </form>
  );
}
