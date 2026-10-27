-- Termos curtos para buscar vagas (ex.: "Analista de Dados"), sugeridos pela IA a partir do
-- perfil. O cargo-alvo descreve o perfil; estes termos são o que funciona em sites de vaga.
alter table public.resume_profiles
  add column search_terms text[] not null default '{}';
