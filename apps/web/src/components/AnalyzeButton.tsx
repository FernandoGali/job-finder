"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { SESSION_EXPIRED } from "@/lib/api";
import { type AnalysisResult, analyzeResume } from "@/lib/resumes";
import { getAccessToken } from "@/lib/supabase/token";

async function requestAnalysis(resumeId: string): Promise<AnalysisResult> {
  const token = await getAccessToken();
  return token ? analyzeResume(token, resumeId) : { state: "error", message: SESSION_EXPIRED };
}

export function AnalyzeButton({
  resumeId,
  label,
  analyze = requestAnalysis,
}: {
  resumeId: string;
  label: string;
  analyze?: (resumeId: string) => Promise<AnalysisResult>;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setBusy(true);
    setError(null);
    const result = await analyze(resumeId);
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
        {busy ? "Analisando… (pode levar até 1 minuto)" : label}
      </button>
      {error && <p role="alert">{error}</p>}
    </div>
  );
}
