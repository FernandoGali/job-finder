"use client";

import { useState } from "react";

import { searchLinks } from "@/lib/jobSearch";

/** Busca pronta: o termo vem do perfil, a pessoa ajusta, e cada botão abre o site da vaga. */
export function JobSearchLinks({ initialQuery }: { initialQuery: string }) {
  const [query, setQuery] = useState(initialQuery);
  const [location, setLocation] = useState("");
  const links = searchLinks(query, location);

  return (
    <section aria-label="Buscar vagas" style={{ display: "grid", gap: 8 }}>
      <h2 style={{ marginBottom: 0 }}>Buscar vagas</h2>
      <p style={{ margin: 0, fontSize: "0.9em" }}>
        Ajuste a busca se quiser. Cada botão abre o site da vaga já com a busca preenchida.
      </p>
      <label>
        O que buscar
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          style={{ display: "block", width: "100%" }}
        />
      </label>
      <label>
        Onde (cidade ou estado, opcional)
        <input
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          placeholder="Ex.: São Paulo"
          style={{ display: "block", width: "100%" }}
        />
      </label>
      {links.length > 0 ? (
        <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {links.map((link) => (
            <li key={link.site}>
              <a href={link.url} target="_blank" rel="noopener noreferrer">
                Buscar no {link.site}
              </a>
            </li>
          ))}
        </ul>
      ) : (
        <p role="status">Escreva o que buscar para ver os links.</p>
      )}
      <p style={{ margin: 0, fontSize: "0.8em" }}>
        O local é usado só no LinkedIn e no Indeed; nos outros sites, escolha a cidade lá.
      </p>
    </section>
  );
}
