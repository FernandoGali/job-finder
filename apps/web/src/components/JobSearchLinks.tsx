"use client";

import { useState } from "react";

import { searchLinks } from "@/lib/jobSearch";

/**
 * Busca pronta: as sugestões vêm da análise do currículo, a pessoa escolhe ou ajusta,
 * e cada botão abre o site da vaga com a busca preenchida.
 */
export function JobSearchLinks({ suggestions }: { suggestions: string[] }) {
  const [query, setQuery] = useState(suggestions[0] ?? "");
  const [location, setLocation] = useState("");
  const [remote, setRemote] = useState(false);
  const links = searchLinks(query, { location, remote });

  return (
    <section aria-label="Buscar vagas" style={{ display: "grid", gap: 8 }}>
      <h2 style={{ marginBottom: 0 }}>Buscar vagas</h2>
      <p style={{ margin: 0, fontSize: "0.9em" }}>
        Escolha uma sugestão ou escreva a sua. Cada botão abre o site da vaga já com a busca
        preenchida.
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
      <label style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <input type="checkbox" checked={remote} onChange={(event) => setRemote(event.target.checked)} />
        Só vagas remotas
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
        O local é usado só no LinkedIn e no Indeed; nos outros sites, escolha a cidade lá. Em
        &quot;Só vagas remotas&quot;, o LinkedIn usa o filtro de trabalho remoto; nos outros, a
        palavra &quot;remoto&quot; entra na busca.
      </p>
    </section>
  );
}
