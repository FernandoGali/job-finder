/**
 * "Busca pronta": links para a busca de vagas de cada site, já preenchida com o perfil.
 *
 * Quem abre o link é a própria pessoa, no navegador dela. O Job Finder não acessa nem
 * coleta nada desses sites (regra 3 do CLAUDE.md).
 */

export type SearchLink = { site: string; url: string };

export type SearchOptions = { location?: string; remote?: boolean };

type Site = { name: string; build: (query: string, location: string, remote: boolean) => string };

/** "Análise de Dados" -> "analise-de-dados", para sites que usam a busca no caminho do link. */
export function slugify(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

const q = encodeURIComponent;

/** Sites sem filtro de remoto no link: a palavra entra no termo de busca. */
const withRemote = (query: string, remote: boolean) => (remote ? `${query} remoto` : query);

// Conferidos em 27/10/2026 (LinkedIn, Vagas.com.br e InfoJobs por requisição; Indeed, Gupy e
// Trampos pelo Fernando no navegador). Glassdoor saiu: o formato testado não preenchia a busca.
const SITES: Site[] = [
  {
    name: "LinkedIn",
    build: (query, location, remote) => {
      // f_WT=2 é o filtro "Remoto" do LinkedIn; sem local, limita ao Brasil.
      const place = location || (remote ? "Brasil" : "");
      return (
        `https://www.linkedin.com/jobs/search/?keywords=${q(query)}` +
        (place ? `&location=${q(place)}` : "") +
        (remote ? "&f_WT=2" : "")
      );
    },
  },
  {
    name: "Indeed",
    build: (query, location, remote) =>
      `https://br.indeed.com/jobs?q=${q(withRemote(query, remote))}` +
      (location ? `&l=${q(location)}` : ""),
  },
  {
    name: "Gupy",
    build: (query, _location, remote) =>
      `https://portal.gupy.io/job-search/term=${q(withRemote(query, remote))}`,
  },
  {
    name: "Vagas.com.br",
    build: (query, _location, remote) =>
      `https://www.vagas.com.br/vagas-de-${slugify(withRemote(query, remote))}`,
  },
  {
    name: "InfoJobs",
    build: (query, _location, remote) =>
      `https://www.infojobs.com.br/vagas-de-emprego-${slugify(withRemote(query, remote))}.aspx`,
  },
  {
    name: "Trampos",
    build: (query, _location, remote) =>
      `https://trampos.co/oportunidades?tr=${q(withRemote(query, remote))}`,
  },
];

export function searchLinks(query: string, { location = "", remote = false }: SearchOptions = {}): SearchLink[] {
  const cleanQuery = query.trim().replace(/\s+/g, " ");
  if (!slugify(cleanQuery)) {
    return [];
  }
  const cleanLocation = location.trim().replace(/\s+/g, " ");
  return SITES.map((site) => ({ site: site.name, url: site.build(cleanQuery, cleanLocation, remote) }));
}
