import { type Profile, SENIORITY_LABELS } from "@/lib/resumes";

/** O que a IA leu no currículo. Campos que ela não conseguiu deduzir aparecem como tal. */
export function ProfileCard({ profile }: { profile: Profile }) {
  return (
    <section
      aria-label="Perfil lido pela IA"
      style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 12, display: "grid", gap: 8 }}
    >
      <dl style={{ margin: 0, display: "grid", gridTemplateColumns: "max-content 1fr", gap: "4px 12px" }}>
        <dt>Cargo-alvo</dt>
        <dd style={{ margin: 0 }}>
          <strong>{profile.target_role ?? "Não identificado no currículo"}</strong>
        </dd>
        <dt>Senioridade</dt>
        <dd style={{ margin: 0 }}>
          {profile.seniority ? SENIORITY_LABELS[profile.seniority] : "Não deu para deduzir"}
        </dd>
      </dl>
      {profile.suggested_roles && profile.suggested_roles.length > 0 && (
        <div>
          <h3 style={{ fontSize: "0.9em", margin: "4px 0" }}>Cargos em que você é mais qualificado</h3>
          <ol aria-label="Cargos sugeridos" style={{ margin: 0, paddingLeft: 20, display: "grid", gap: 6 }}>
            {profile.suggested_roles.map((role) => (
              <li key={role.title}>
                <strong>{role.title}</strong>
                {role.evidence && (
                  <div style={{ fontSize: "0.85em", color: "#4b5563" }}>No currículo: “{role.evidence}”</div>
                )}
                {role.keywords.length > 0 && (
                  <ul
                    aria-label={`Palavras-chave para ${role.title}`}
                    style={{ listStyle: "none", margin: "4px 0 0", padding: 0, display: "flex", flexWrap: "wrap", gap: 6 }}
                  >
                    {role.keywords.map((keyword) => (
                      <li
                        key={keyword}
                        style={{ background: "#ecfdf5", borderRadius: 999, padding: "2px 10px", fontSize: "0.85em" }}
                      >
                        {keyword}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ol>
        </div>
      )}
      <div>
        <h3 style={{ fontSize: "0.9em", margin: "4px 0" }}>Competências no currículo</h3>
        {profile.skills.length > 0 ? (
          <ul
            aria-label="Competências"
            style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexWrap: "wrap", gap: 6 }}
          >
            {profile.skills.map((skill) => (
              <li
                key={skill}
                style={{ background: "#eef2ff", borderRadius: 999, padding: "2px 10px", fontSize: "0.85em" }}
              >
                {skill}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ margin: 0 }}>Nenhuma competência identificada.</p>
        )}
      </div>
      {profile.certifications.length > 0 && (
        <div>
          <h3 style={{ fontSize: "0.9em", margin: "4px 0" }}>Cursos e certificações</h3>
          <ul aria-label="Cursos e certificações" style={{ margin: 0, paddingLeft: 20, fontSize: "0.9em" }}>
            {profile.certifications.map((certification) => (
              <li key={certification}>{certification}</li>
            ))}
          </ul>
        </div>
      )}
      {profile.summary && <p style={{ margin: 0, fontSize: "0.9em" }}>{profile.summary}</p>}
    </section>
  );
}
