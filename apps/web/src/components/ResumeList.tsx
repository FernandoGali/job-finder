import type { ResumesResult } from "@/lib/resumes";

const dateFormat = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Sao_Paulo",
});

export function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}

export function ResumeList({ result }: { result: ResumesResult }) {
  if (result.state === "error") {
    return <p role="alert">{result.message}</p>;
  }
  if (result.resumes.length === 0) {
    return <p>Você ainda não enviou nenhum currículo.</p>;
  }

  const [latest, ...older] = result.resumes;
  return (
    <section aria-label="Meus currículos">
      <h2>Meu currículo</h2>
      <p>
        <strong>{latest.original_filename}</strong> · {formatSize(latest.size_bytes)} · enviado em{" "}
        {dateFormat.format(new Date(latest.uploaded_at))}
      </p>
      {older.length > 0 && (
        <details>
          <summary>Envios anteriores ({older.length})</summary>
          <ul>
            {older.map((resume) => (
              <li key={resume.id}>
                {resume.original_filename} · {dateFormat.format(new Date(resume.uploaded_at))}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
