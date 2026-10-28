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
- No radar: limitar as análises de currículo pela IA por plano (cada uma custa alguns centavos de dólar na API da Anthropic). Hoje a análise só roda no clique em "Analisar" (decisão do Fernando, para não gastar com envios por engano) e não tem limite; o limite deve ser conferido na API (`POST /curriculos/{id}/analise`), não só na tela.

## Estado atual e próximo passo

- Feito: fase 0 — estrutura do monorepo, `/health` na API, página inicial no Next.js, testes e CI verdes.
- Feito: projeto Supabase criado (São Paulo; Data API ligada, exposição automática de tabelas desligada, RLS automático ligado). Chaves no `.env` da raiz, que a API e o Next.js leem.
- Feito: login parte 1 — `/entrar` (e-mail e senha), `/auth/callback`, `/minha-area` protegida pelo middleware. Testado à mão pelo Fernando.
- Feito: confirmação de e-mail por botão em `/auth/confirmar` (resistente aos robôs de link do Outlook/Hotmail), aviso de `?erro=link` no `/entrar`, regra de senha com checklist ao vivo no cadastro. Testado à mão pelo Fernando.
- Feito: login parte 2 — a API confere o JWT do Supabase (ES256, chave pública via JWKS, sem segredo) em `auth.py`; rotas que exigem login usam `Depends(get_current_user)`. `/me` devolve quem está logado e a Minha área mostra a resposta. Testado à mão pelo Fernando.
- Feito: parte 3a — tabelas `consents` e `resumes` e pasta privada `curriculos` no Storage, com RLS (cada usuário só acessa `<user_id>/...`). Aplicado no projeto real e conferido de fora (visitante não acessa nada).
- Feito: parte 3b — `POST /curriculos` e `GET /curriculos` na API: login + consentimento (termo `v1`), PDF/DOCX até 5 MB detectados pelo conteúdo, nome aleatório no Storage, grava com o token do usuário (o RLS vale para a API).
- Feito: parte 3c — Minha área com termo, envio e lista dos currículos; o navegador envia direto para a API. Testado de ponta a ponta pelo Fernando (arquivo no Storage e registro em `resumes`).
- Feito: excluir currículo (`DELETE /curriculos/{id}`: arquivo antes do registro) e conta (`DELETE /conta`: arquivos da pasta, depois a conta com a chave secreta; o resto vai em cascata). Na tela: botão Excluir com confirmação e seção que exige digitar EXCLUIR. Testado à mão pelo Fernando (inclusive excluir a própria conta e criar outra).
- Feito: análise pela IA — `POST /curriculos/{id}/analise` extrai o texto (pypdf / python-docx), pede ao Claude (`claude-opus-5-5`, saída em JSON Schema, effort `medium`, `fallbacks: "default"`) cargo-alvo, senioridade, competências, cursos e certificações (campo próprio: nome de curso não entra como competência; migração `20261028150000` aplicada e testado pelo Fernando) e resumo, e confere tudo contra o texto (`ground_in_resume`: competência como palavra inteira, cargo só com evidência copiada do currículo). O perfil fica em `resume_profiles`, gravado só pela API com a chave secreta. A análise só roda no clique em "Analisar" na Minha área (não é automática no envio). Migração aplicada no projeto real e testado à mão pelo Fernando. A chave local da Anthropic (`job-finder-local`, workspace Default) vence em 26/11/2026; vencida, a análise responde "Não foi possível analisar" e é só criar outra e trocar no `.env`.
- Ao escrever arquivos pelas ferramentas do Claude, a sequência barra-invertida + u + 4 dígitos vira o caractere de verdade (aconteceu na regex de acentos de `jobSearch.ts`). Para escrever o escape literal, montar o texto em pedaços (ex.: `String.fromCharCode(92)`).
- API local: rodar o uvicorn sem `--reload` no Windows; o recarregamento deixava processos órfãos presos na porta 8000 servindo código antigo.
- Feito: busca pronta — bloco "Buscar vagas" na Minha área (aparece depois da análise). Os termos vêm de `search_terms` da análise (2 a 4 títulos de vaga comuns no Brasil, sugeridos pela IA; `clean_search_terms` tira palavras de nível — júnior, pleno, sênior, jr, sr — e descarta termos com menos de 2 ou mais de 4 palavras, "ou", vírgula, barra ou parênteses), viram botões de sugestão e o campo é editável. Local opcional (só LinkedIn e Indeed usam) e LinkedIn busca a frase exata (termo entre aspas, porque sem elas trazia vagas com só parte das palavras), Indeed busca só no título (`title:(...)`, confirmado pelo Fernando), campo "Nível" (começa com a senioridade do perfil; LinkedIn `f_E`, Indeed `sc=0kf:explvl(...)` ou `jt=internship` para estágio — códigos de memória, aguardando teste do Fernando), caixa "Só vagas remotas (LinkedIn)" (`f_WT=2`, local Brasil por padrão; nos outros sites o filtro é feito no próprio site). Links em `apps/web/src/lib/jobSearch.ts` para LinkedIn, Indeed, Gupy, Vagas.com.br, InfoJobs e Trampos. Só front-end: quem abre o site é a pessoa. Glassdoor saiu (o formato testado não preenchia a busca); Nube e 99jobs ficaram de fora. Lição do teste do Fernando: usar o cargo-alvo inteiro como termo dava poucas ou nenhuma vaga. Medido no Vagas.com.br/InfoJobs: "analista de dados" 207/2.904 vagas; com "júnior" 68/135; com "remoto" 5/138 — por isso nível e remoto não entram no termo.
- Busca pronta tem limite: cada site ordena do jeito dele (anúncios pagos no topo, busca solta) e o Fernando ainda achou muita vaga genérica. Não investir mais em ajustes de link; o ganho real vem do conector, onde nós filtramos e ordenamos.
- Fontes de vagas (28/10/2026): Adzuna exige licença para produto com receita, só entrega trecho da descrição e a conta grátis tem 25 chamadas de teste (acesso completo: £8/mês, 5.000 chamadas/mês). Ficou para depois; conta criada pelo Fernando, chaves ainda não usadas. Escolhida a Greenhouse: API pública de quadros de vagas ("Job Board data is publicly available"; robots.txt só bloqueia /embed/), grátis, descrição completa, cobre só as empresas da lista `GREENHOUSE_BOARDS` em `job_sources.py`.
- Feito: conector fatia 1 (coleta) — tabela `jobs` (fechada para usuários; só a API com a chave secreta), `job_sources.py` lê e normaliza a Greenhouse, `job_sync.py` grava/atualiza e apaga as vagas fechadas; falha numa fonte não apaga nada dela. Rodar à mão: `python -m jobfinder_api.job_sync` em `apps/api`. Leitura real em 28/10: 517 vagas (Stone 361, QuintoAndar 109, VTEX 33, Wildlife 14), ~25 de dados/BI, a maioria sênior.
- Próximo: conector fatia 2 (ranking das vagas contra o perfil, com o motivo de combinar) e fatia 3 (tela "Vagas para você": título, empresa, cidade, resumo curto e link para a vaga na fonte). Depois, coleta automática.
- Termo de consentimento: o texto fica em `apps/web/src/lib/resumes.ts`. Mudou o texto? Subir `CONSENT_VERSION` lá e na API (`resumes.py`) juntos.

## Banco de dados

- Mudanças no banco ficam em `supabase/migrations/` (SQL) e são testadas com pgTAP em `supabase/tests/`. O job "Banco (Supabase)" do CI sobe um Supabase descartável e roda os testes; não há Docker no PC do Fernando.
- Aplicar no projeto real só depois do CI verde: o Fernando cola o SQL no **SQL Editor** do Supabase e roda uma vez. Como não usamos `supabase db push`, o histórico de migrações do projeto real fica vazio; se um dia adotarmos o CLI, marcar as já aplicadas com `supabase migration repair`.
- Tabelas novas: sempre `enable row level security`, `revoke all ... from anon, authenticated` e `grant` só do necessário (a exposição automática de tabelas está desligada).
- E-mail: Supabase envia pelo Resend (SMTP), remetente provisório `onboarding@resend.dev`, que só entrega no e-mail do dono da conta Resend. Modelo "Confirm sign up" aponta para `/auth/confirmar?token_hash=…&type=email` (confirmação só no clique do botão, por causa dos robôs de link do Outlook).
- Senha: mínimo 8 caracteres, com minúscula, maiúscula e número (escolha do Fernando), no Supabase e na tela (`lib/auth/password.ts`). As duas regras precisam andar juntas.
- Pendente: secrets no GitHub quando o CI precisar do Supabase; domínio próprio no Resend antes de abrir para usuários (aí criar uma chave restrita ao domínio e apagar a atual); bloqueio de senhas vazadas (só no plano pago do Supabase); trocar Site URL e Redirect URLs do Supabase para o domínio de produção; política de privacidade citando os operadores dos dados (Supabase, Resend e Anthropic, que lê o currículo na análise); na hospedagem de produção, avaliar federação de identidade da Anthropic (sem chave fixa) no lugar da `ANTHROPIC_API_KEY` local.

## Comandos

```bash
# API
cd apps/api && python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]" && pytest && ruff check . && ruff format --check .

# Web
cd apps/web && npm install && npm test && npm run typecheck && npm run build
```
