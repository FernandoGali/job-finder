-- Vagas também da Lever (API pública de vagas), além da Greenhouse.
alter table public.jobs drop constraint jobs_source_check;
alter table public.jobs add constraint jobs_source_check check (source in ('greenhouse', 'lever'));
