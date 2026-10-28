import { type JobMatchesResult, WORK_MODE_LABELS } from "@/lib/jobs";

// Mesma escala da API (job_matching.py): a partir de 30 a vaga entra na lista.
const STRONG_MATCH = 60;

/** Vagas para você: pouco texto e sempre o link para a vaga na fonte (regra 4). */
export function JobMatches({ result }: { result: JobMatchesResult }) {
  if (result.state === "no-profile") {
    return null;
  }

  return (
    <section aria-label="Vagas para você" style={{ display: "grid", gap: 8 }}>
      <h2 style={{ marginBottom: 0 }}>Vagas para você</h2>
      {result.state === "error" ? (
        <p role="alert">{result.message}</p>
      ) : result.jobs.length === 0 ? (
        <p>
          Nenhuma vaga combina com o seu perfil agora. Novas vagas entram todo dia; enquanto
          isso, use a busca em outros sites abaixo.
        </p>
      ) : (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 8 }}>
          {result.jobs.map((job) => (
            <li
              key={job.id}
              style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 12, display: "grid", gap: 4 }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <strong>{job.title}</strong>
                <span
                  style={{
                    whiteSpace: "nowrap",
                    fontSize: "0.8em",
                    borderRadius: 999,
                    padding: "2px 8px",
                    background: job.score >= STRONG_MATCH ? "#dcfce7" : "#eef2ff",
                    alignSelf: "start",
                  }}
                >
                  {job.score >= STRONG_MATCH ? "Combina muito" : "Combina"}
                </span>
              </div>
              <span style={{ fontSize: "0.9em" }}>
                {job.company}
                {job.location ? ` · ${job.location}` : ""}
                {job.work_mode && (
                  <>
                    {" · "}
                    <strong>{WORK_MODE_LABELS[job.work_mode]}</strong>
                  </>
                )}
              </span>
              <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.85em" }}>
                {job.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
              <a href={job.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: "0.9em" }}>
                Ver vaga e candidatar-se
              </a>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
