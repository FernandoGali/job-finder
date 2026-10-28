"use client";

import { useActionState, useState } from "react";

import type { ConfirmParams } from "@/lib/auth/confirm";
import { PASSWORD_MIN_LENGTH, passwordProblem } from "@/lib/auth/password";

import { PasswordChecklist } from "./PasswordChecklist";

type ResetState = { error: string | null };

export function ResetPasswordForm({
  params,
  action,
}: {
  params: ConfirmParams;
  action: (previous: ResetState, formData: FormData) => Promise<ResetState>;
}) {
  const [state, formAction, pending] = useActionState(action, { error: null });
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");

  const mismatch = confirmation !== "" && confirmation !== password;
  const ready = !passwordProblem(password) && confirmation === password;

  return (
    <form action={formAction} style={{ display: "grid", gap: 12, maxWidth: 360 }}>
      <h1>Criar senha nova</h1>
      <input type="hidden" name="token_hash" value={params.tokenHash} />
      <input type="hidden" name="type" value={params.type} />
      <label>
        Senha nova
        <input
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={PASSWORD_MIN_LENGTH}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          style={{ width: "100%" }}
        />
      </label>
      <PasswordChecklist password={password} />
      <label>
        Repita a senha nova
        <input
          name="confirmation"
          type="password"
          autoComplete="new-password"
          value={confirmation}
          onChange={(event) => setConfirmation(event.target.value)}
          required
          style={{ width: "100%" }}
        />
      </label>
      {mismatch && <p role="status">As duas senhas ainda não são iguais.</p>}
      <button type="submit" disabled={!ready || pending}>
        {pending ? "Salvando…" : "Salvar senha nova"}
      </button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
