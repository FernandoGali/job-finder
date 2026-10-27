"use client";

import { type FormEvent, useState } from "react";

import {
  ACCEPT_ATTRIBUTE,
  CONSENT_TEXT,
  fileProblem,
  type Resume,
  type UploadResult,
} from "@/lib/resumes";

type Feedback = { kind: "error" | "info"; text: string };

export function ResumeUploadForm({
  upload,
  onUploaded,
}: {
  upload: (file: File) => Promise<UploadResult>;
  onUploaded: (resume: Resume) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  function handleFile(selected: File | null) {
    setFile(selected);
    const problem = selected ? fileProblem(selected) : null;
    setFeedback(problem ? { kind: "error", text: problem } : null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!file || !consent || fileProblem(file)) {
      return;
    }

    setBusy(true);
    setFeedback(null);
    const result = await upload(file);
    setBusy(false);

    if (result.state === "error") {
      setFeedback({ kind: "error", text: result.message });
      return;
    }
    setFeedback({
      kind: "info",
      text: result.notice ?? `Currículo "${result.resume.original_filename}" enviado!`,
    });
    setFile(null);
    form.reset();
    onUploaded(result.resume);
  }

  const ready = file !== null && consent && !fileProblem(file);
  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 480 }}>
      <h2 style={{ margin: 0 }}>Enviar currículo</h2>
      <label>
        Arquivo (PDF ou DOCX, até 5 MB)
        <input
          name="file"
          type="file"
          accept={ACCEPT_ATTRIBUTE}
          onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
          style={{ display: "block", marginTop: 4 }}
        />
      </label>
      <label style={{ display: "flex", gap: 8, alignItems: "flex-start", fontSize: "0.9em" }}>
        <input
          name="consent"
          type="checkbox"
          checked={consent}
          onChange={(event) => setConsent(event.target.checked)}
          style={{ marginTop: 3 }}
        />
        <span>{CONSENT_TEXT}</span>
      </label>
      <button type="submit" disabled={!ready || busy}>
        {busy ? "Enviando e analisando…" : "Enviar currículo"}
      </button>
      {feedback && <p role={feedback.kind === "error" ? "alert" : "status"}>{feedback.text}</p>}
    </form>
  );
}
