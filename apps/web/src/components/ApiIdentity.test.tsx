import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ApiIdentity } from "./ApiIdentity";

describe("ApiIdentity", () => {
  it("confirma quando a API reconhece a pessoa", () => {
    render(<ApiIdentity result={{ state: "ok", me: { id: "1", email: "ana@exemplo.com" } }} />);

    expect(screen.getByRole("status")).toHaveTextContent("A API reconheceu você (ana@exemplo.com)");
  });

  it("pede para entrar de novo quando a API recusa a sessão", () => {
    render(<ApiIdentity result={{ state: "unauthorized" }} />);

    expect(screen.getByRole("status")).toHaveTextContent("Saia e entre de novo");
  });

  it("avisa quando a API está fora do ar", () => {
    render(<ApiIdentity result={{ state: "offline", reason: "fetch failed" }} />);

    expect(screen.getByRole("status")).toHaveTextContent("API fora do ar (fetch failed)");
  });
});
