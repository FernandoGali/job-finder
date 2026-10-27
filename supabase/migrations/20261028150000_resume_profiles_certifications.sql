-- Cursos, treinamentos e certificações ficam separados das competências no perfil.
alter table public.resume_profiles
  add column certifications text[] not null default '{}';
