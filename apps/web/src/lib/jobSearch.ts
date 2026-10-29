/**
 * "Busca pronta": links para a busca de vagas de cada site, já preenchida com o perfil.
 *
 * Quem abre o link é a própria pessoa, no navegador dela. O Job Finder não acessa nem
 * coleta nada desses sites (regra 3 do CLAUDE.md).
 */

import type { Seniority } from "./resumes";

export type SearchLink = { site: string; url: string };

export type SearchOptions = { location?: string; remote?: boolean; level?: Seniority | null };

type Options = { location: string; remote: boolean; level: Seniority | null };

type Site = { name: string; build: (query: string, options: Options) => string };

// Filtro "Nível de experiência" do LinkedIn (f_E): 1 Estágio, 2 Assistente, 3 Júnior,
// 4 Pleno-sênior, 5 Diretor, 6 Executivo.
const LINKEDIN_LEVELS: Record<Seniority, string> = {
  estagio: "1",
  junior: "2,3",
  pleno: "4",
  senior: "4",
  especialista: "4",
  gestao: "5,6",
};

// Indeed: estágio é tipo de vaga (jt=internship); os demais usam o nível de experiência.
const INDEED_LEVELS: Record<Seniority, string> = {
  estagio: "&jt=internship",
  junior: `&sc=${encodeURIComponent("0kf:explvl(ENTRY_LEVEL);")}`,
  pleno: `&sc=${encodeURIComponent("0kf:explvl(MID_LEVEL);")}`,
  senior: `&sc=${encodeURIComponent("0kf:explvl(SENIOR_LEVEL);")}`,
  especialista: `&sc=${encodeURIComponent("0kf:explvl(SENIOR_LEVEL);")}`,
  gestao: `&sc=${encodeURIComponent("0kf:explvl(SENIOR_LEVEL);")}`,
};

/** "Análise de Dados" -> "analise-de-dados", para sites que usam a busca no caminho do link. */
export function slugify(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Remotar: números internos das tags de nível (t=) e das áreas (c=), lidos pelo Fernando nos
// filtros do site em 29/10/2026. Gestão não tem tag de nível lá.
const REMOTAR_LEVELS: Partial<Record<Seniority, string>> = {
  estagio: "10",
  junior: "17",
  pleno: "21",
  senior: "23",
  especialista: "23",
};

// Área do Remotar pelas palavras do cargo (sem acento, minúsculas), na ordem: a primeira regra que
// bate vale. As mais específicas vêm antes ("mobile" antes de "desenvolvedor", "ux" antes de
// "design"). "Analista de Qualidade" é qualidade industrial, não QA de software: por isso QA só
// com "qa", "tester" ou "testes". Sem regra que bata, o link vai sem área (melhor que chutar).
const REMOTAR_AREAS: [string[], string][] = [
  [["dados", "data", "bi", "analytics", "cientista"], "4"],
  [["qa", "tester", "testes"], "8"],
  [["devops", "sre"], "7"],
  [["sysadmin", "infraestrutura", "redes"], "9"],
  [["mobile", "android", "ios", "flutter"], "14"],
  [["desenvolvedor", "desenvolvedora", "programador", "developer", "software", "backend", "frontend", "fullstack"], "13"],
  [["ux", "ui"], "6"],
  [["motion"], "11"],
  [["design", "designer"], "5"],
  [["produto", "product"], "15"],
  [["seo", "conteudo", "redator", "redatora", "copywriter"], "3"],
  [["marketing", "growth"], "10"],
  [["vendas", "comercial", "sdr", "negocios", "vendedor"], "17"],
  [["rh", "recrutador", "recrutadora", "recrutamento", "people"], "16"],
  [["suporte", "atendimento", "sucesso"], "2"],
  [["juridico", "advogado", "advogada"], "19"],
  [["professor", "professora", "educacao", "instrutor", "pedagogo"], "22"],
  [["comunicacao", "jornalista"], "20"],
  [["midia"], "21"],
  [["financeiro", "financeira", "administrativo", "administrativa", "operacoes", "contabil", "fiscal"], "1"],
];

/** Área do Remotar para o termo de busca, ou null se nenhuma regra bater. */
export function remotarArea(query: string): string | null {
  const words = new Set(slugify(query).split("-"));
  if (words.has("recursos") && words.has("humanos")) {
    return "16";
  }
  return REMOTAR_AREAS.find(([keys]) => keys.some((key) => words.has(key)))?.[1] ?? null;
}

const q = encodeURIComponent;

// Conferidos em 27/10/2026 (LinkedIn, Vagas.com.br e InfoJobs por requisição; Indeed, Gupy e
// Trampos pelo Fernando no navegador). Glassdoor saiu: o formato testado não preenchia a busca.
// "Só remotas" vale só no LinkedIn, que tem filtro oficial. Nos outros, pôr "remoto" no termo
// quase zerava a busca (Vagas.com.br: 207 vagas de analista de dados, 5 com "remoto").
const SITES: Site[] = [
  {
    name: "LinkedIn",
    build: (query, { location, remote, level }) => {
      // Entre aspas, o LinkedIn busca a frase exata; sem elas, aceita anúncios com só parte
      // das palavras (ex.: "Analista de Suporte" numa busca de BI).
      const phrase = `"${query.replace(/"/g, "")}"`;
      // f_WT=2 é o filtro "Remoto" do LinkedIn; sem local, limita ao Brasil.
      const place = location || (remote ? "Brasil" : "");
      return (
        `https://www.linkedin.com/jobs/search/?keywords=${q(phrase)}` +
        (place ? `&location=${q(place)}` : "") +
        (remote ? "&f_WT=2" : "") +
        (level ? `&f_E=${q(LINKEDIN_LEVELS[level])}` : "")
      );
    },
  },
  {
    name: "Indeed",
    // title:(...) é a busca avançada do Indeed: todas as palavras no título da vaga, o que
    // corta anúncios genéricos que só citam o termo na descrição.
    build: (query, { location, level }) =>
      `https://br.indeed.com/jobs?q=${q(`title:(${query.replace(/[()"]/g, "")})`)}` +
      (location ? `&l=${q(location)}` : "") +
      (level ? INDEED_LEVELS[level] : ""),
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
  {
    // Só vagas remotas. Formato conferido pelo Fernando no navegador em 29/10/2026, com "+" no
    // lugar dos espaços; só o nome do cargo filtra mal, por isso vão também a área (c) e a tag
    // de nível (t). A coleta automática do Remotar não é permitida pelos termos de uso deles; o
    // link é só para a pessoa abrir.
    name: "Remotar",
    build: (query, { level }) => {
      const params = new URLSearchParams({ q: query });
      const area = remotarArea(query);
      if (area) {
        params.set("c", area);
      }
      const tag = level && REMOTAR_LEVELS[level];
      if (tag) {
        params.set("t", tag);
      }
      return `https://remotar.com.br/search/jobs?${params}`;
    },
  },
];

export function searchLinks(
  query: string,
  { location = "", remote = false, level = null }: SearchOptions = {},
): SearchLink[] {
  const cleanQuery = query.trim().replace(/\s+/g, " ");
  if (!slugify(cleanQuery)) {
    return [];
  }
  const options = { location: location.trim().replace(/\s+/g, " "), remote, level };
  return SITES.map((site) => ({ site: site.name, url: site.build(cleanQuery, options) }));
}
