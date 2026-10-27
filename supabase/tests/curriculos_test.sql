-- Testes das regras de acesso de currículos. Rodam no CI com `supabase test db`.
-- Tudo acontece dentro de uma transação desfeita no fim: nada fica no banco.
begin;
create extension if not exists pgtap with schema extensions;

select plan(17);

-- Cenário: Ana (A) e Bia (B). Os dados da Bia são criados como administrador.
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'ana@exemplo.com'),
  ('22222222-2222-2222-2222-222222222222', 'bia@exemplo.com');

insert into public.consents (id, user_id, purpose, version) values
  ('33333333-3333-3333-3333-333333333333', '22222222-2222-2222-2222-222222222222', 'analise_curriculo', 'v1');

insert into public.resumes (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
values ('22222222-2222-2222-2222-222222222222', '33333333-3333-3333-3333-333333333333',
        '22222222-2222-2222-2222-222222222222/cv.pdf', 'cv.pdf', 'application/pdf', 1000);

insert into storage.objects (bucket_id, name)
values ('curriculos', '22222222-2222-2222-2222-222222222222/cv.pdf');

-- Faz as próximas consultas rodarem como um usuário logado.
create function pg_temp.entrar_como(uid uuid) returns void language sql as $$
  select set_config('role', 'authenticated', true);
  select set_config('request.jwt.claims',
    json_build_object('sub', uid, 'role', 'authenticated')::text, true);
$$;

-- Pasta -------------------------------------------------------------------------

select is(
  (select public from storage.buckets where id = 'curriculos'), false,
  'a pasta de currículos é privada'
);

-- Consentimento -------------------------------------------------------------------

select pg_temp.entrar_como('11111111-1111-1111-1111-111111111111');

select lives_ok(
  $$ insert into public.consents (user_id, purpose, version)
     values ('11111111-1111-1111-1111-111111111111', 'analise_curriculo', 'v1') $$,
  'Ana registra o próprio consentimento'
);

select throws_ok(
  $$ insert into public.consents (user_id, purpose, version)
     values ('22222222-2222-2222-2222-222222222222', 'analise_curriculo', 'v1') $$,
  '42501', null,
  'Ana não registra consentimento em nome da Bia'
);

select throws_ok(
  $$ insert into public.consents (user_id, purpose, version, granted_at)
     values ('11111111-1111-1111-1111-111111111111', 'analise_curriculo', 'v1', '2000-01-01') $$,
  '42501', null,
  'Ana não escolhe a data do consentimento'
);

select is(
  (select count(*) from public.consents), 1::bigint,
  'Ana só vê o próprio consentimento'
);

-- Registro do currículo -------------------------------------------------------------

select lives_ok(
  $$ insert into public.resumes (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
     values ('11111111-1111-1111-1111-111111111111',
             (select id from public.consents),
             '11111111-1111-1111-1111-111111111111/cv.pdf', 'cv.pdf', 'application/pdf', 1000) $$,
  'Ana registra o próprio currículo'
);

select throws_ok(
  $$ insert into public.resumes (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
     values ('11111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333',
             '11111111-1111-1111-1111-111111111111/outro.pdf', 'outro.pdf', 'application/pdf', 1000) $$,
  '42501', null,
  'Ana não usa o consentimento da Bia'
);

select throws_ok(
  $$ insert into public.resumes (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
     values ('22222222-2222-2222-2222-222222222222', (select id from public.consents),
             '22222222-2222-2222-2222-222222222222/falso.pdf', 'falso.pdf', 'application/pdf', 1000) $$,
  '42501', null,
  'Ana não registra currículo em nome da Bia'
);

select throws_ok(
  $$ insert into public.resumes (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
     values ('11111111-1111-1111-1111-111111111111', (select id from public.consents),
             '22222222-2222-2222-2222-222222222222/cv2.pdf', 'cv2.pdf', 'application/pdf', 1000) $$,
  null, null,
  'Ana não aponta o registro para a pasta da Bia'
);

select throws_ok(
  $$ insert into public.resumes (user_id, consent_id, storage_path, original_filename, content_type, size_bytes)
     values ('11111111-1111-1111-1111-111111111111', (select id from public.consents),
             '11111111-1111-1111-1111-111111111111/foto.png', 'foto.png', 'image/png', 1000) $$,
  '23514', null,
  'só aceita PDF e DOCX'
);

select is(
  (select count(*) from public.resumes), 1::bigint,
  'Ana só vê o próprio currículo'
);

select lives_ok(
  $$ delete from public.resumes where user_id = '22222222-2222-2222-2222-222222222222' $$,
  'apagar o currículo da Bia não dá erro...'
);

-- Arquivos no Storage ---------------------------------------------------------------

select lives_ok(
  $$ insert into storage.objects (bucket_id, name)
     values ('curriculos', '11111111-1111-1111-1111-111111111111/cv.pdf') $$,
  'Ana envia arquivo para a própria pasta'
);

select throws_ok(
  $$ insert into storage.objects (bucket_id, name)
     values ('curriculos', '22222222-2222-2222-2222-222222222222/intruso.pdf') $$,
  '42501', null,
  'Ana não envia arquivo para a pasta da Bia'
);

select is(
  (select count(*) from storage.objects where bucket_id = 'curriculos'), 1::bigint,
  'Ana só vê os próprios arquivos'
);

-- Visitante sem login ---------------------------------------------------------------

reset role;
select set_config('role', 'anon', true);
select set_config('request.jwt.claims', '{"role": "anon"}', true);

select throws_ok(
  $$ select count(*) from public.consents $$,
  '42501', null,
  'visitante sem login não acessa consentimentos'
);

-- Conferência final como administrador -----------------------------------------------

reset role;

select is(
  (select count(*) from public.resumes where user_id = '22222222-2222-2222-2222-222222222222'),
  1::bigint,
  '...mas o currículo da Bia continua lá'
);

select * from finish();
rollback;
