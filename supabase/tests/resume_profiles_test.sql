-- Testes das regras de acesso do perfil extraído pela IA.
begin;
create extension if not exists pgtap with schema extensions;

select plan(5);

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
  $$ insert into public.resume_profiles (resume_id, user_id, target_role, seniority, skills, model) values
     ('c1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
      'Analista de Dados', 'pleno', array['SQL', 'Python'], 'claude-opus-5-5'),
     ('d2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222',
      'Designer', 'junior', array['Figma'], 'claude-opus-5-5') $$,
  'a API grava perfis com a chave secreta'
);
reset role;

-- Ana logada.
select set_config('role', 'authenticated', true);
select set_config('request.jwt.claims',
  '{"sub": "11111111-1111-1111-1111-111111111111", "role": "authenticated"}', true);

select is(
  (select array_agg(target_role) from public.resume_profiles),
  array['Analista de Dados'],
  'Ana só vê o próprio perfil'
);

select throws_ok(
  $$ update public.resume_profiles set seniority = 'senior' $$,
  '42501', null,
  'Ana não altera o resultado da análise'
);

select throws_ok(
  $$ insert into public.resume_profiles (resume_id, user_id, model) values
     ('c1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'forjado') $$,
  '42501', null,
  'Ana não grava um perfil por conta própria'
);

reset role;

-- Apagar o currículo apaga o perfil junto.
delete from public.resumes where id = 'c1111111-1111-1111-1111-111111111111';
select is(
  (select count(*) from public.resume_profiles where user_id = '11111111-1111-1111-1111-111111111111'),
  0::bigint,
  'excluir o currículo exclui o perfil'
);

select * from finish();
rollback;
