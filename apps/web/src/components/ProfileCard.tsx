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
      {profile.summary && <p style={{ margin: 0, fontSize: "0.9em" }}>{profile.summary}</p>}
    </section>
  );
}
