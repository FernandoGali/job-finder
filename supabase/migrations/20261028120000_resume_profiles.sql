-- Perfil extraído do currículo pela IA (leitura no estilo ATS).
--
-- A pessoa só lê o próprio perfil. Quem grava é a API com a chave secreta, depois
-- de conferir a resposta da IA: assim ninguém forja o resultado pelo navegador.

create table public.resume_profiles (
  resume_id uuid primary key references public.resumes (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  target_role text,
  seniority text check (
    seniority in ('estagio', 'junior', 'pleno', 'senior', 'especialista', 'gestao')
  ),
  skills text[] not null default '{}',
  summary text not null default '',
  model text not null,
  analyzed_at timestamptz not null default now()
);

create index resume_profiles_user_id_idx on public.resume_profiles (user_id);

alter table public.resume_profiles enable row level security;

revoke all on public.resume_profiles from anon, authenticated;
grant select on public.resume_profiles to authenticated;
grant all on public.resume_profiles to service_role;

create policy "resume_profiles: ver os próprios"
  on public.resume_profiles for select to authenticated
  using ((select auth.uid()) = user_id);
