import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiStatusBadge } from "./ApiStatusBadge";

describe("ApiStatusBadge", () => {
  it("mostra a versão e o ambiente quando a API está no ar", () => {
    render(
      <ApiStatusBadge
        status={{
          state: "online",
          health: { status: "ok", version: "0.1.0", env: "staging", supabase_configured: true },
        }}
      />,
    );

    const badge = screen.getByRole("status");
    expect(badge).toHaveAttribute("data-state", "online");
    expect(badge).toHaveTextContent("v0.1.0");
    expect(badge).toHaveTextContent("staging");
    expect(badge).toHaveTextContent("Supabase configurado");
  });

  it("avisa quando o Supabase ainda não foi configurado", () => {
    render(
      <ApiStatusBadge
        status={{
          state: "online",
          health: { status: "ok", version: "0.1.0", env: "development", supabase_configured: false },
        }}
      />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("ainda não configurado");
  });

  it("mostra o motivo quando a API está fora do ar", () => {
    render(<ApiStatusBadge status={{ state: "offline", reason: "HTTP 503" }} />);

    const badge = screen.getByRole("status");
    expect(badge).toHaveAttribute("data-state", "offline");
    expect(badge).toHaveTextContent("HTTP 503");
  });
});
