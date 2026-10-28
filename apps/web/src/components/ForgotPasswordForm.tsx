"use client";

import { type FormEvent, useState } from "react";

import { authErrorMessage } from "@/lib/auth/messages";

type SendResult = { error: { code?: string } | null };

// Mesmo texto exista a conta ou não: ninguém descobre quais e-mails têm cadastro.
const SENT =
  "Se houver uma conta com esse e-mail, enviamos um link para redefinir a senha. Confira a " +
  "caixa de entrada e o lixo eletrônico.";

// Só o limite de envios é mostrado; outros erros também viram a mensagem neutra.
const SHOWN_ERRORS = new Set(["over_email_send_rate_limit", "over_request_rate_limit"]);

export function ForgotPasswordForm({
  send,
  notice,
}: {
  send: (email: string) => Promise<SendResult>;
  notice?: string;
}) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<{ kind: "error" | "info"; text: string } | null>(
    notice ? { kind: "error", text: notice } : null,
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(new FormData(event.currentTarget).get("email"));
    setBusy(true);
    setFeedback(null);
    const { error } = await send(email);
    setBusy(false);
    if (error?.code && SHOWN_ERRORS.has(error.code)) {
      setFeedback({ kind: "error", text: authErrorMessage(error) });
    } else {
      setFeedback({ kind: "info", text: SENT });
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 360 }}>
      <h1>Esqueci minha senha</h1>
      <p style={{ margin: 0 }}>Informe o e-mail da sua conta. Vamos enviar um link para criar uma senha nova.</p>
      <label>
        E-mail
        <input name="email" type="email" autoComplete="email" required style={{ width: "100%" }} />
      </label>
      <button type="submit" disabled={busy}>
        {busy ? "Enviando…" : "Enviar link"}
      </button>
      {feedback && <p role={feedback.kind === "error" ? "alert" : "status"}>{feedback.text}</p>}
      <a href="/entrar" style={{ fontSize: "0.9em" }}>
        Voltar para entrar
      </a>
    </form>
  );
}
