"use client";

import { useFormStatus } from "react-dom";

import type { ConfirmParams } from "@/lib/auth/confirm";

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? "Confirmando…" : "Confirmar meu e-mail"}
    </button>
  );
}

export function ConfirmEmailForm({
  params,
  action,
}: {
  params: ConfirmParams;
  action: (formData: FormData) => void | Promise<void>;
}) {
  return (
    <form action={action} style={{ display: "grid", gap: 12, maxWidth: 360 }}>
      <h1>Confirmar e-mail</h1>
      <p>Falta só um clique para ativar sua conta.</p>
      <input type="hidden" name="token_hash" value={params.tokenHash} />
      <input type="hidden" name="type" value={params.type} />
      <SubmitButton />
    </form>
  );
}
