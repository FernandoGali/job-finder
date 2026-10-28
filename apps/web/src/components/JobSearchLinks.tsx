"use client";

import { useState } from "react";

import { searchLinks } from "@/lib/jobSearch";
import { type Seniority, SENIORITY_LABELS } from "@/lib/resumes";

/**
 * Busca pronta: as sugestões vêm da análise do currículo, a pessoa escolhe ou ajusta,
 * e cada botão abre o site da vaga com a busca preenchida.
 */
export function JobSearchLinks({
  suggestions,
  seniority = null,
}: {
  suggestions: string[];
  seniority?: Seniority | null;
}) {
  const [query, setQuery] = useState(suggestions[0] ?? "");
  const [location, setLocation] = useState("");
  const [remote, setRemote] = useState(false);
  const [level, setLevel] = useState<Seniority | null>(seniority);
  const links = searchLinks(query, { location, remote, level });

  return (
    <section aria-label="Buscar em outros sites" style={{ display: "grid", gap: 8 }}>
      <h2 style={{ marginBottom: 0 }}>Buscar em outros sites</h2>
      <p style={{ margin: 0, fontSize: "0.9em" }}>
        Para ir além das vagas acima: escolha uma sugestão ou escreva a sua. Cada botão abre o
        site já com a busca preenchida.
      </p>
      {suggestions.length > 0 && (
        <div role="group" aria-label="Sugestões de busca" style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {suggestions.map((term) => (
            <button key={term} type="button" aria-pressed={term === query} onClick={() => setQuery(term)}>
              {term}
            </button>
          ))}
        </div>
      )}
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
      <label>
        Nível (LinkedIn e Indeed)
        <select
          value={level ?? ""}
          onChange={(event) => setLevel((event.target.value || null) as Seniority | null)}
          style={{ display: "block" }}
        >
          <option value="">Qualquer nível</option>
          {(Object.keys(SENIORITY_LABELS) as Seniority[]).map((key) => (
            <option key={key} value={key}>
              {SENIORITY_LABELS[key]}
            </option>
          ))}
        </select>
      </label>
      <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input type="checkbox" checked={remote} onChange={(event) => setRemote(event.target.checked)} />
        Só vagas remotas (LinkedIn)
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
        O local e o nível são usados só no LinkedIn e no Indeed. Nos outros sites, escolha a
        cidade, o nível (júnior, pleno…) e a modalidade (remoto, híbrido) nos filtros do próprio
        site.
      </p>
    </section>
  );
}
