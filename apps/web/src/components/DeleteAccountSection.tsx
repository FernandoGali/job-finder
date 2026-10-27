"use client";

import { type FormEvent, useState } from "react";

import type { ActionResult } from "@/lib/api";

const CONFIRMATION_WORD = "EXCLUIR";

/** Exclusão da conta (LGPD). Pede para digitar EXCLUIR, porque não tem volta. */
export function DeleteAccountSection({
  deleteAccount,
  onDeleted,
}: {
  deleteAccount: () => Promise<ActionResult>;
  onDeleted: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (typed !== CONFIRMATION_WORD) {
      return;
    }
    setBusy(true);
    setError(null);
    const result = await deleteAccount();
    if (result.state === "error") {
      setBusy(false);
      setError(result.message);
      return;
    }
    onDeleted();
  }

  return (
    <section aria-label="Excluir conta" style={{ borderTop: "1px solid #e5e7eb", paddingTop: 16 }}>
      <h2 style={{ fontSize: "1em" }}>Excluir minha conta</h2>
      <p style={{ fontSize: "0.9em" }}>
        Apaga sua conta, todos os currículos enviados e o registro do seu consentimento. Não dá
        para desfazer.
      </p>
      {!open ? (
        <button type="button" onClick={() => setOpen(true)}>
          Quero excluir minha conta
        </button>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: 8, maxWidth: 360 }}>
          <label>
            Para confirmar, digite {CONFIRMATION_WORD}
            <input
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              autoComplete="off"
              style={{ display: "block", width: "100%" }}
            />
          </label>
          <button type="submit" disabled={typed !== CONFIRMATION_WORD || busy}>
            {busy ? "Excluindo…" : "Excluir minha conta definitivamente"}
          </button>
          <button type="button" onClick={() => setOpen(false)} disabled={busy}>
            Cancelar
          </button>
          {error && <p role="alert">{error}</p>}
        </form>
      )}
    </section>
  );
}
