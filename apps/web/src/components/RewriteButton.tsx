"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { SESSION_EXPIRED } from "@/lib/api";
import { type RewriteResult, rewriteResume } from "@/lib/resumes";
import { getAccessToken } from "@/lib/supabase/token";

async function requestRewrite(resumeId: string): Promise<RewriteResult> {
  const token = await getAccessToken();
  return token ? rewriteResume(token, resumeId) : { state: "error", message: SESSION_EXPIRED };
}

/** Só roda no clique: cada reescrita é uma chamada maior (e mais cara) à IA. */
export function RewriteButton({
  resumeId,
  label,
  rewrite = requestRewrite,
}: {
  resumeId: string;
  label: string;
  rewrite?: (resumeId: string) => Promise<RewriteResult>;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setBusy(true);
    setError(null);
    const result = await rewrite(resumeId);
    setBusy(false);
    if (result.state === "error") {
      setError(result.message);
      return;
    }
    router.refresh();
  }

  return (
    <div>
      <button type="button" onClick={handleClick} disabled={busy}>
        {busy ? "Reescrevendo… (pode levar até 2 minutos)" : label}
      </button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
