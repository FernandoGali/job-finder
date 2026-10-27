/**
 * "Busca pronta": links para a busca de vagas de cada site, já preenchida com o perfil.
 *
 * Quem abre o link é a própria pessoa, no navegador dela. O Job Finder não acessa nem
 * coleta nada desses sites (regra 3 do CLAUDE.md).
 */

export type SearchLink = { site: string; url: string };

type Site = { name: string; build: (query: string, location: string) => string };

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

// Conferidos em 27/10/2026. Se um site mudar o formato do link, ajustar aqui.
const SITES: Site[] = [
  {
    name: "LinkedIn",
    build: (query, location) =>
      `https://www.linkedin.com/jobs/search/?keywords=${q(query)}` +
      (location ? `&location=${q(location)}` : ""),
  },
  {
    name: "Indeed",
    build: (query, location) =>
      `https://br.indeed.com/jobs?q=${q(query)}` + (location ? `&l=${q(location)}` : ""),
  },
  {
    name: "Glassdoor",
    build: (query) => `https://www.glassdoor.com.br/Vaga/vagas.htm?sc.keyword=${q(query)}`,
  },
  {
    name: "Gupy",
    build: (query) => `https://portal.gupy.io/job-search/term=${q(query)}`,
  },
  {
    name: "Vagas.com.br",
    build: (query) => `https://www.vagas.com.br/vagas-de-${slugify(query)}`,
  },
  {
    name: "InfoJobs",
    build: (query) => `https://www.infojobs.com.br/vagas-de-emprego-${slugify(query)}.aspx`,
  },
  {
    name: "Trampos",
    build: (query) => `https://trampos.co/oportunidades?tr=${q(query)}`,
  },
];

export function searchLinks(query: string, location = ""): SearchLink[] {
  const cleanQuery = query.trim().replace(/\s+/g, " ");
  if (!slugify(cleanQuery)) {
    return [];
  }
  const cleanLocation = location.trim().replace(/\s+/g, " ");
  return SITES.map((site) => ({ site: site.name, url: site.build(cleanQuery, cleanLocation) }));
}
