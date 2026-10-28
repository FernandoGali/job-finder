-- Vagas coletadas das fontes (hoje: quadros públicos da Greenhouse).
--
-- A tabela fica fechada para usuários: só a API lê e grava, com a chave secreta. A descrição
-- completa é usada só para comparar com o currículo; a tela mostra pouco e linka sempre
-- para a vaga na fonte (regra 4 do CLAUDE.md).

create table public.jobs (
  id uuid primary key default gen_random_uuid(),
  source text not null check (source in ('greenhouse')),
  board text not null,
  external_id text not null,
  company text not null,
  title text not null,
  location text not null default '',
  description text not null default '',
  url text not null check (url like 'https://%'),
  published_at timestamptz,
  updated_at timestamptz,
  fetched_at timestamptz not null default now(),
  unique (source, external_id)
);

create index jobs_source_board_idx on public.jobs (source, board);

alter table public.jobs enable row level security;

revoke all on public.jobs from anon, authenticated;
grant all on public.jobs to service_role;
