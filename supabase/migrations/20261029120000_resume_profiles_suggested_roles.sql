-- Os 3 cargos para os quais a pessoa está mais qualificada, sugeridos pela IA. Cada item:
-- {"title": "...", "evidence": "trecho do currículo" | null, "keywords": ["...", ...]}.
-- Os títulos continuam copiados em search_terms, que a busca de vagas usa.
alter table public.resume_profiles
  add column suggested_roles jsonb not null default '[]'
    check (jsonb_typeof(suggested_roles) = 'array');
