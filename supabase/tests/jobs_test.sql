-- Testes das regras de acesso da tabela de vagas.
begin;
create extension if not exists pgtap with schema extensions;

select plan(7);

set local role service_role;
select lives_ok(
  $$ insert into public.jobs (source, board, external_id, company, title, location, description, url)
     values ('greenhouse', 'exemplo', '1', 'Exemplo', 'Analista de Dados', 'Brasil',
             'Descrição completa', 'https://job-boards.greenhouse.io/exemplo/jobs/1') $$,
  'a API grava vagas com a chave secreta'
);

select throws_ok(
  $$ insert into public.jobs (source, board, external_id, company, title, url)
     values ('greenhouse', 'exemplo', '1', 'Exemplo', 'Repetida', 'https://x.io/1') $$,
  '23505', null,
  'a mesma vaga da mesma fonte não entra duas vezes'
);

select throws_ok(
  $$ insert into public.jobs (source, board, external_id, company, title, url)
     values ('greenhouse', 'exemplo', '2', 'Exemplo', 'Link inseguro', 'javascript:alert(1)') $$,
  '23514', null,
  'o link da vaga precisa ser https'
);

select lives_ok(
  $$ insert into public.jobs (source, board, external_id, company, title, url)
     values ('lever', 'exemplo', '1', 'Exemplo', 'Analista de Dados', 'https://jobs.lever.co/exemplo/1') $$,
  'a Lever também é uma fonte aceita'
);

select throws_ok(
  $$ insert into public.jobs (source, board, external_id, company, title, url)
     values ('gupy', 'exemplo', '1', 'Exemplo', 'Analista', 'https://x.io/1') $$,
  '23514', null,
  'fonte fora da lista não entra'
);
reset role;

-- Usuário logado não lê a tabela direto: a descrição completa é só para uso interno.
select set_config('role', 'authenticated', true);
select set_config('request.jwt.claims',
  '{"sub": "11111111-1111-1111-1111-111111111111", "role": "authenticated"}', true);
select throws_ok(
  $$ select count(*) from public.jobs $$,
  '42501', null,
  'usuário logado não acessa a tabela de vagas'
);
reset role;

select set_config('role', 'anon', true);
select throws_ok(
  $$ select count(*) from public.jobs $$,
  '42501', null,
  'visitante sem login não acessa a tabela de vagas'
);

select * from finish();
rollback;
