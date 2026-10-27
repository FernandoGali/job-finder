# Job Finder

Suba o currículo uma vez e receba as vagas mais aderentes, com score de compatibilidade e as palavras-chave que faltam.

O plano completo (arquitetura, fontes, planos, roadmap) está no documento do projeto: *Plataforma de Vagas por Currículo — Arquitetura e Plano*.

## Estrutura

```
apps/
  api/   API em FastAPI (Python 3.12)
  web/   Frontend em Next.js
.github/workflows/ci.yml   testes automáticos a cada push
docker-compose.yml         Postgres (com pgvector) e Redis para desenvolvimento
```

Os workers de coleta e análise entram na fase 1.

## Regras do projeto

- **Toda feature entra com testes automatizados**, e todo bug corrigido ganha um teste que o reproduz.
- O CI roda tudo a cada push; teste falhando bloqueia a publicação.
- **Senhas e chaves nunca vão para o código nem para o chat.** Ficam no `.env` local (fora do Git) e nos *secrets* do GitHub e da hospedagem.
- Coleta de vagas só onde os termos permitem; o resto entra como busca pronta (link).

## Rodando localmente

Pré-requisitos: Python 3.12+, Node 22+ e Docker.

```bash
cp .env.example .env          # preencha os valores
docker compose up -d          # banco e Redis

# API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                        # testes
uvicorn jobfinder_api.main:app --reload   # http://localhost:8000/health

# Frontend (outro terminal)
cd apps/web
npm install
npm test
npm run dev                   # http://localhost:3000
```
