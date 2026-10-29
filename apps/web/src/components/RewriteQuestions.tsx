"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { SESSION_EXPIRED } from "@/lib/api";
import { type RewriteAnswer, type RewriteResult, rewriteResume } from "@/lib/resumes";
import { getAccessToken } from "@/lib/supabase/token";

async function requestRewrite(resumeId: string, answers: RewriteAnswer[]): Promise<RewriteResult> {
  const token = await getAccessToken();
  return token ? rewriteResume(token, resumeId, answers) : { state: "error", message: SESSION_EXPIRED };
}

/** As perguntas da reescrita, com um campo para cada resposta. As respostas viram fatos da próxima. */
export function RewriteQuestions({
  resumeId,
  questions,
  rewrite = requestRewrite,
}: {
  resumeId: string;
  questions: string[];
  rewrite?: (resumeId: string, answers: RewriteAnswer[]) => Promise<RewriteResult>;
}) {
  const router = useRouter();
  const [answers, setAnswers] = useState<string[]>(() => questions.map(() => ""));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const filled = questions
    .map((question, index) => ({ question, answer: answers[index].trim() }))
    .filter((item) => item.answer);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    const result = await rewrite(resumeId, filled);
    setBusy(false);
    if (result.state === "error") {
      setError(result.message);
      return;
    }
    router.refresh();
  }

  return (
    <form
      onSubmit={handleSubmit}
      aria-label="Perguntas para fortalecer o currículo"
      style={{ marginTop: 8, background: "#fef3c7", borderRadius: 8, padding: 8, display: "grid", gap: 8 }}
    >
      <h4 style={{ fontSize: "0.95em", margin: 0 }}>Para deixar seu currículo mais forte</h4>
      <p style={{ margin: 0, fontSize: "0.85em" }}>
        Não inventamos números nem resultados. Responda o que souber (pode deixar em branco) e reescreva: as respostas
        entram no currículo como informação sua.
      </p>
      {questions.map((question, index) => (
        <label key={question} style={{ display: "grid", gap: 4 }}>
          {question}
          <textarea
            value={answers[index]}
            onChange={(event) =>
              setAnswers((current) => current.map((value, i) => (i === index ? event.target.value : value)))
            }
            maxLength={1000}
            rows={2}
            style={{ font: "inherit" }}
          />
        </label>
      ))}
      <button type="submit" disabled={busy || filled.length === 0}>
        {busy ? "Reescrevendo… (pode levar até 2 minutos)" : "Reescrever com minhas respostas"}
      </button>
      {error && <p role="alert">{error}</p>}
    </form>
  );
}
