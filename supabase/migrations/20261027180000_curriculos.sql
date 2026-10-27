-- Currículos: consentimento LGPD, registro dos arquivos e pasta privada no Storage.
--
-- A API grava em nome do usuário (com o token dele), então estas regras (RLS) são a
-- garantia final de que cada pessoa só lê e grava os próprios dados.

-- Consentimento ---------------------------------------------------------------

create table public.consents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  purpose text not null check (purpose in ('analise_curriculo')),
  version text not null check (version <> ''),
  granted_at timestamptz not null default now()
);

create index consents_user_id_idx on public.consents (user_id);

alter table public.consents enable row level security;

-- Permissões explícitas: nada de herdar acesso padrão. A data do aceite é sempre a do
-- banco, por isso o usuário só pode preencher estas três colunas.
revoke all on public.consents from anon, authenticated;
grant select on public.consents to authenticated;
grant insert (user_id, purpose, version) on public.consents to authenticated;
grant all on public.consents to service_role;

create policy "consents: ver os próprios"
  on public.consents for select to authenticated
  using ((select auth.uid()) = user_id);

create policy "consents: registrar os próprios"
  on public.consents for insert to authenticated
  with check ((select auth.uid()) = user_id);

-- Currículos enviados ---------------------------------------------------------

create table public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  consent_id uuid not null references public.consents (id) on delete cascade,
  storage_path text not null unique,
  original_filename text not null check (char_length(original_filename) between 1 and 255),
  content_type text not null check (
    content_type in (
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
  ),
  size_bytes integer not null check (size_bytes between 1 and 5242880),
  uploaded_at timestamptz not null default now(),
  -- O arquivo sempre fica na pasta do próprio dono: "<user_id>/<arquivo>".
  constraint resumes_path_in_owner_folder check (storage_path like user_id::text || '/%')
);

create index resumes_user_id_idx on public.resumes (user_id);

alter table public.resumes enable row level security;

revoke all on public.resumes from anon, authenticated;
grant select, delete on public.resumes to authenticated;
grant insert (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
  on public.resumes to authenticated;
grant all on public.resumes to service_role;

create policy "resumes: ver os próprios"
  on public.resumes for select to authenticated
  using ((select auth.uid()) = user_id);

create policy "resumes: registrar os próprios, com o próprio consentimento"
  on public.resumes for insert to authenticated
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1 from public.consents c
      where c.id = consent_id and c.user_id = (select auth.uid())
    )
  );

create policy "resumes: apagar os próprios"
  on public.resumes for delete to authenticated
  using ((select auth.uid()) = user_id);

-- Pasta privada no Storage ----------------------------------------------------

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'curriculos',
  'curriculos',
  false,
  5242880,
  array[
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ]
)
on conflict (id) do nothing;

-- Cada usuário só mexe em "curriculos/<seu user_id>/...". Sem regra de update:
-- um arquivo enviado não pode ser sobrescrito, só apagado e enviado de novo.
create policy "curriculos: ver os próprios"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'curriculos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "curriculos: enviar para a própria pasta"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'curriculos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );

create policy "curriculos: apagar os próprios"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'curriculos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
