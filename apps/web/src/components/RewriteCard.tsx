import type { ResumeRewrite } from "@/lib/resumes";

const sectionTitle = { fontSize: "0.95em", margin: "8px 0 4px", borderBottom: "1px solid #e5e7eb" } as const;

/** O currículo reescrito, no formato que os sistemas de triagem leem bem: uma coluna e seções padrão. */
export function RewriteCard({ rewrite }: { rewrite: ResumeRewrite }) {
  return (
    <section
      aria-label="Currículo reescrito para ATS"
      style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 12, display: "grid", gap: 4 }}
    >
      <h3 style={{ margin: 0 }}>Currículo reescrito para ATS</h3>
      <p style={{ margin: 0, fontSize: "0.85em", color: "#4b5563" }}>
        Conferimos cada empresa, cargo, data e número com o seu currículo original: o que não estava lá ficou de
        fora.
      </p>
      {rewrite.headline && <p style={{ margin: "4px 0 0", fontWeight: 600 }}>{rewrite.headline}</p>}

      {rewrite.summary && (
        <>
          <h4 style={sectionTitle}>Resumo</h4>
          <p style={{ margin: 0 }}>{rewrite.summary}</p>
        </>
      )}

      {rewrite.experiences.length > 0 && (
        <>
          <h4 style={sectionTitle}>Experiência</h4>
          {rewrite.experiences.map((experience, index) => (
            <div key={`${experience.company}-${index}`}>
              <strong>{[experience.role, experience.company].filter(Boolean).join(" · ")}</strong>
              {experience.period && <span style={{ color: "#4b5563" }}> · {experience.period}</span>}
              <ul style={{ margin: "2px 0 6px", paddingLeft: 20 }}>
                {experience.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            </div>
          ))}
        </>
      )}

      {rewrite.education.length > 0 && (
        <>
          <h4 style={sectionTitle}>Formação</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {rewrite.education.map((item, index) => (
              <li key={`${item.institution}-${index}`}>
                {[item.course, item.institution, item.period].filter(Boolean).join(" · ")}
              </li>
            ))}
          </ul>
        </>
      )}

      {rewrite.skills.length > 0 && (
        <>
          <h4 style={sectionTitle}>Competências</h4>
          <p style={{ margin: 0 }}>{rewrite.skills.join(" · ")}</p>
        </>
      )}

      {rewrite.certifications.length > 0 && (
        <>
          <h4 style={sectionTitle}>Cursos e certificações</h4>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {rewrite.certifications.map((certification) => (
              <li key={certification}>{certification}</li>
            ))}
          </ul>
        </>
      )}

      {rewrite.questions.length > 0 && (
        <div style={{ marginTop: 8, background: "#fef3c7", borderRadius: 8, padding: 8 }}>
          <h4 style={{ fontSize: "0.95em", margin: "0 0 4px" }}>Para deixar seu currículo mais forte</h4>
          <p style={{ margin: 0, fontSize: "0.85em" }}>
            Não inventamos números nem resultados. Se você souber estas respostas, inclua no currículo:
          </p>
          <ul aria-label="Perguntas para fortalecer o currículo" style={{ margin: "4px 0 0", paddingLeft: 20 }}>
            {rewrite.questions.map((question) => (
              <li key={question}>{question}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
