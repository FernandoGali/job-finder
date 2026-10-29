-- Testes das regras de acesso do currículo reescrito pela IA.
begin;
create extension if not exists pgtap with schema extensions;

select plan(6);

insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'ana@exemplo.com'),
  ('22222222-2222-2222-2222-222222222222', 'bia@exemplo.com');

insert into public.consents (id, user_id, purpose, version) values
  ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'analise_curriculo', 'v1'),
  ('b2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'analise_curriculo', 'v1');

insert into public.resumes (id, user_id, consent_id, storage_path, original_filename, content_type, size_bytes) values
  ('c1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
   'a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111/cv.pdf',
   'cv.pdf', 'application/pdf', 1000),
  ('d2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222',
   'b2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222/cv.pdf',
   'cv.pdf', 'application/pdf', 1000);

-- Gravado como a API grava (papel de serviço).
set local role service_role;
select lives_ok(
  $$ insert into public.resume_rewrites (resume_id, user_id, content, model) values
     ('c1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
      '{"summary": "Ana"}', 'claude-opus-5-5'),
     ('d2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222',
      '{"summary": "Bia"}', 'claude-opus-5-5') $$,
  'a API grava reescritas com a chave secreta'
);

select throws_ok(
  $$ insert into public.resume_rewrites (resume_id, user_id, content, model) values
     ('c1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
      '["não é objeto"]', 'claude-opus-5-5')
     on conflict (resume_id) do update set content = excluded.content $$,
  '23514', null,
  'o conteúdo precisa ser um objeto JSON'
);
reset role;

-- Ana logada.
select set_config('role', 'authenticated', true);
select set_config('request.jwt.claims',
  '{"sub": "11111111-1111-1111-1111-111111111111", "role": "authenticated"}', true);

select is(
  (select array_agg(content ->> 'summary') from public.resume_rewrites),
  array['Ana'],
  'Ana só vê a própria reescrita'
);

select throws_ok(
  $$ update public.resume_rewrites set content = '{}' $$,
  '42501', null,
  'Ana não altera a reescrita pelo navegador'
);

select throws_ok(
  $$ insert into public.resume_rewrites (resume_id, user_id, content, model) values
     ('c1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', '{}', 'forjado') $$,
  '42501', null,
  'Ana não grava uma reescrita por conta própria'
);

reset role;

-- Apagar o currículo apaga a reescrita junto.
delete from public.resumes where id = 'c1111111-1111-1111-1111-111111111111';
select is(
  (select count(*) from public.resume_rewrites where user_id = '11111111-1111-1111-1111-111111111111'),
  0::bigint,
  'excluir o currículo exclui a reescrita'
);

select * from finish();
rollback;
