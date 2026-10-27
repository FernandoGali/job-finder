import { PASSWORD_RULES } from "@/lib/auth/password";

/** Lista as regras da senha e marca com uma bolinha verde as que já foram cumpridas. */
export function PasswordChecklist({ password }: { password: string }) {
  return (
    <ul aria-label="Regras da senha" style={{ listStyle: "none", margin: 0, padding: 0 }}>
      {PASSWORD_RULES.map((rule) => {
        const ok = rule.ok(password);
        return (
          <li
            key={rule.label}
            data-ok={ok}
            style={{ display: "flex", alignItems: "center", gap: 6, fontSize: "0.85em" }}
          >
            <span
              aria-hidden="true"
              style={{
                flexShrink: 0,
                width: 8,
                height: 8,
                boxSizing: "border-box",
                borderRadius: "50%",
                border: `1px solid ${ok ? "#16a34a" : "#9ca3af"}`,
                background: ok ? "#16a34a" : "transparent",
                transition: "background 150ms, border-color 150ms",
              }}
            />
            <span style={{ color: ok ? "#16a34a" : undefined }}>{rule.label}</span>
            <span style={visuallyHidden}>{ok ? "(ok)" : "(falta)"}</span>
          </li>
        );
      })}
    </ul>
  );
}

// Texto só para leitores de tela: quem não enxerga a cor também sabe o que falta.
const visuallyHidden = {
  position: "absolute",
  width: 1,
  height: 1,
  overflow: "hidden",
  clip: "rect(0 0 0 0)",
  whiteSpace: "nowrap",
} as const;
