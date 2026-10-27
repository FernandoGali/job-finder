# Job Finder — contexto para o Claude

Plataforma multiusuário: a pessoa sobe o currículo, a IA faz a leitura no estilo ATS, extrai cargo-alvo, competências e senioridade, e a aplicação busca vagas em fontes pré-definidas e devolve uma lista ranqueada com o motivo de cada vaga combinar.

O plano completo (arquitetura, fluxo, modelo de dados, API, planos, fontes, roadmap) está no documento "Plataforma de Vagas por Currículo — Arquitetura e Plano", no claude.ai: https://claude.ai/artifact/4LpL3VL6z2krykQFfrEH8G

## Como trabalhamos

- O Fernando traz as ideias e valida cada entrega; o Claude escreve o código.
- Trabalhar em fatias pequenas e testáveis (uma tela, um endpoint, um conector). Mostrar o resultado e esperar aprovação antes da próxima fatia.
- Explicar em português, de forma simples: o Fernando está aprendendo o fluxo de desenvolvimento.
- Quando um passo depender dele (criar conta, gerar chave, aprovar publicação), avisar e dar o passo a passo.

## Regras inegociáveis

1. **Testes automatizados sempre.** Toda feature entra com testes; todo bug corrigido ganha um teste que o reproduz. Nada é validado só na mão. O CI (GitHub Actions) roda tudo a cada push e teste falhando bloqueia publicação.
2. **Segredos nunca no código nem no chat.** Senhas e chaves ficam no `.env` local (fora do Git) e nos secrets do GitHub/hospedagem. Nunca pedir que o Fernando cole uma chave na conversa.
3. **Nunca burlar regras dos sites de vagas.** Só coletar onde os termos permitem ou há autorização por escrito. Sem login, sem proxy para fugir de limite, sem resolver captcha. Respeitar `robots.txt`. Se um site bloquear, desligar o conector. O resto entra como "busca pronta" (link para a busca do site já preenchida com o perfil).
4. **Mostrar pouco, linkar sempre.** A descrição completa da vaga só é usada internamente para o matching; o painel mostra título, empresa, cidade, um resumo curto e o botão para a vaga na fonte (ex.: "Candidatar-se na Gupy").
5. **LGPD.** Consentimento no upload, exclusão real da conta, sem coletar dados pessoais de terceiros (recrutadores) das vagas.
6. **IA não inventa.** Na extração e na reescrita do currículo, nunca inventar empresa, cargo, data ou número.

## Stack e decisões

- Backend: Python 3.12 + FastAPI (`apps/api`). Lint com ruff, testes com pytest (cobertura mínima 90%).
- Frontend: Next.js + TypeScript (`apps/web`). Testes com Vitest + Testing Library.
- Supabase: login (Supabase Auth), banco (Postgres com pgvector) e arquivos (Supabase Storage), região São Paulo.
- Workers (fase 1): Celery + Redis para análise do currículo, coleta e ranking.
- IA: Claude API com saída estruturada (schema JSON) para extrair o perfil.
- Local: `docker-compose.yml` sobe Postgres (pgvector) e Redis.

## Fontes de vagas (checagem de 27/10/2026)

- Candidatas a conector: Gupy (passar pela checagem de termos e robots.txt antes do primeiro uso), Novo Trampo (termos não proíbem), Nerdin (dados estruturados; pedir ok).
- Busca pronta: LinkedIn, Indeed, Glassdoor (termos proíbem coleta), vagas.com.br (exige autorização), InfoJobs (bloqueia robôs), Trampos, 99jobs, Nube (termos não localizados).
- Alternativas sem contato: API oficial da Adzuna, páginas de carreira com JSON-LD `JobPosting`, ATS com API pública (Greenhouse, Lever).

## Planos (valores provisórios, revisar após análise de custos)

- Grátis: 1 busca por semana. Básico R$ 10/mês: 1 busca por dia. Pro R$ 30/mês: 5 buscas por dia + 4 ajustes de currículo por mês.
- Resultados sem limite em todos. Reescrita ATS avulsa em DOCX: R$ 10.

## Estado atual e próximo passo

- Feito: fase 0 — estrutura do monorepo, `/health` na API, página inicial no Next.js, testes e CI verdes.
- Próximo: criar o projeto no Supabase (o Fernando cria a conta), configurar as chaves no `.env` e nos secrets, e implementar login + upload do currículo, com testes.

## Comandos

```bash
# API
cd apps/api && python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]" && pytest && ruff check . && ruff format --check .

# Web
cd apps/web && npm install && npm test && npm run typecheck && npm run build
```
