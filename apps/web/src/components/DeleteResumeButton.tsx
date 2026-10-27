"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { type ActionResult, callApi, SESSION_EXPIRED } from "@/lib/api";
import { getAccessToken } from "@/lib/supabase/token";

async function removeResume(resumeId: string): Promise<ActionResult> {
  const token = await getAccessToken();
  if (!token) {
    return { state: "error", message: SESSION_EXPIRED };
  }
  return callApi("DELETE", `/curriculos/${resumeId}`, token);
}

export function DeleteResumeButton({
  resumeId,
  filename,
  remove = removeResume,
  confirm = (message: string) => window.confirm(message),
}: {
  resumeId: string;
  filename: string;
  remove?: (resumeId: string) => Promise<ActionResult>;
  confirm?: (message: string) => boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    if (!confirm(`Excluir o currículo "${filename}"? Isso não pode ser desfeito.`)) {
      return;
    }
    setBusy(true);
    setError(null);
    const result = await remove(resumeId);
    setBusy(false);
    if (result.state === "error") {
      setError(result.message);
      return;
    }
    router.refresh();
  }

  return (
    <>
      <button type="button" onClick={handleClick} disabled={busy}>
        {busy ? "Excluindo…" : "Excluir"}
      </button>
      {error && <span role="alert"> {error}</span>}
    </>
  );
}
