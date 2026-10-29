-- Currículo reescrito pela IA para sistemas de triagem (ATS), um por currículo enviado.
--
-- Mesmas regras do perfil: a pessoa só lê a própria reescrita, e quem grava é a API com a
-- chave secreta, depois de conferir o texto contra o currículo original (a IA não inventa).

create table public.resume_rewrites (
  resume_id uuid primary key references public.resumes (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  content jsonb not null check (jsonb_typeof(content) = 'object'),
  model text not null,
  created_at timestamptz not null default now()
);

create index resume_rewrites_user_id_idx on public.resume_rewrites (user_id);

alter table public.resume_rewrites enable row level security;

revoke all on public.resume_rewrites from anon, authenticated;
grant select on public.resume_rewrites to authenticated;
grant all on public.resume_rewrites to service_role;

create policy "resume_rewrites: ver as próprias"
  on public.resume_rewrites for select to authenticated
  using ((select auth.uid()) = user_id);
