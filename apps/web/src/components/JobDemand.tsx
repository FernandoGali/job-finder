import type { JobDemandResult } from "@/lib/jobs";

/** O que as vagas pedem para cada cargo sugerido: contagem em vagas reais, sem IA. */
export function JobDemand({ result }: { result: JobDemandResult }) {
  if (result.state === "no-profile" || (result.state === "ok" && result.roles.length === 0)) {
    return null;
  }

  return (
    <section aria-label="O que as vagas pedem" style={{ display: "grid", gap: 8 }}>
      <h2 style={{ marginBottom: 0 }}>O que as vagas pedem</h2>
      {result.state === "error" ? (
        <p role="alert">{result.message}</p>
      ) : (
        <>
          <p style={{ margin: 0, fontSize: "0.9em", color: "#4b5563" }}>
            Nas vagas coletadas de cada cargo, as ferramentas, métodos e idiomas mais pedidos: os que, juntos,
            somam 80% dos pedidos.
          </p>
          {result.roles.map((role) => (
            <div
              key={role.role}
              style={{ border: "1px solid #e5e7eb", borderRadius: 8, padding: 12, display: "grid", gap: 6 }}
            >
              <h3 style={{ fontSize: "1em", margin: 0 }}>
                {role.role}{" "}
                <span style={{ fontWeight: "normal", fontSize: "0.85em", color: "#4b5563" }}>
                  · {role.jobs} {role.jobs === 1 ? "vaga" : "vagas"}
                </span>
              </h3>
              {role.items.length === 0 ? (
                <p style={{ margin: 0, fontSize: "0.9em" }}>
                  Poucas vagas desse cargo nas empresas acompanhadas para calcular o que é mais pedido.
                </p>
              ) : (
                <ul
                  aria-label={`Mais pedidos para ${role.role}`}
                  style={{ listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 4 }}
                >
                  {role.items.map((item) => (
                    <li
                      key={item.name}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "minmax(0, 1fr) auto auto",
                        gap: 8,
                        alignItems: "center",
                        fontSize: "0.9em",
                      }}
                    >
                      <span>{item.name}</span>
                      <span style={{ color: "#4b5563" }}>{item.share}% das vagas</span>
                      <span
                        style={{
                          borderRadius: 999,
                          padding: "2px 8px",
                          fontSize: "0.85em",
                          background: item.in_resume ? "#dcfce7" : "#fef3c7",
                        }}
                      >
                        {item.in_resume ? "✓ No seu currículo" : "Não está no currículo"}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </>
      )}
    </section>
  );
}
