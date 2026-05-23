## Summary

O SPARK é uma plataforma de busca de produções científicas da UNEB que orquestra um pipeline ETL sobre XMLs do Lattes (Apache Hop), enriquece os dados com Qualis CAPES, CrossRef e OpenAlex, e expõe duas modalidades de busca via API FastAPI: textual (Full-Text Search com `tsvector`/GIN no PostgreSQL) e semântica (embeddings `all-MiniLM-L6-v2` + similaridade de cosseno via `pgvector`). O front-end Next.js consome a API REST e exibe os resultados em cards responsivos com indicadores bibliométricos.

---

## Technical Context

**Language/Version:** Python 3.11 (back-end), Node.js 20 / TypeScript (front-end)

**Primary Dependencies:**

* Back-end: FastAPI, asyncpg, sentence-transformers (`all-MiniLM-L6-v2`), pgvector, pydantic, uvicorn
* ETL: Apache Hop (pipeline), JDBC PostgreSQL driver
* Front-end: Next.js 14, Tailwind CSS
* Banco: Supabase (PostgreSQL 15 gerenciado) com extensão `pgvector`

**Storage:** Supabase (PostgreSQL + pgvector). Tabelas: `pesquisadores`, `producoes`, `vetores`, `etl_logs`, `perfis`, `auth.users`

**Testing:** pytest (back-end), Jest (front-end)

**Target Platform:** Railway (back-end), Vercel (front-end), Supabase (banco)

**Project Type:** Web application (backend API + frontend)

**Performance Goals:**

* `POST /api/search/text` < 30 segundos de resposta
* `POST /api/search/semantic` < 5 segundos de resposta

**Constraints:**

* Geração de embeddings exclusivamente local (modelo `all-MiniLM-L6-v2`), sem APIs pagas
* Paginação máxima de 20 itens por página em todas as listagens
* RLS habilitado em todas as tabelas do Supabase
* Acesso de leitura às produções e pesquisadores é sempre público (sem autenticação)
* Autenticação apenas para o papel Admin (Supabase Auth)

**Scale/Scope:** Produções científicas de pesquisadores da UNEB; testado com mínimo de 3 currículos Lattes reais no Sprint II

---

## Constitution Check

*Verificado contra `constitution.md` antes do início de cada fase.*

| Princípio                                      | Status | Observação                                                           |
| ----------------------------------------------- | ------ | ---------------------------------------------------------------------- |
| Acesso público para busca (sem autenticação) | PASS   | Leitura pública via RLS em `pesquisadores`e `producoes`           |
| Embeddings locais sem APIs pagas                | PASS   | Modelo `all-MiniLM-L6-v2`via sentence-transformers                   |
| UPSERT obrigatório em toda escrita ETL         | PASS   | `ON CONFLICT DO UPDATE`em `pesquisadores`e `producoes`           |
| Métricas nunca calculadas em tempo de consulta | PASS   | `total_producoes`,`indice_h`,`total_a1_a2`pré-calculados no ETL |
| `tsvector`mantido por trigger automático     | PASS   | Trigger em `producoes`a cada INSERT/UPDATE                           |
| RLS ativo em todas as tabelas                   | PASS   | `etl_logs`restrito ao admin; demais com leitura pública             |
| Remoção de pesquisador em cascata             | PASS   | Produções e vetores removidos junto                                  |
| Worker de embeddings idempotente                | PASS   | Processa somente `producoes`sem registro em `vetores`              |
| Commits referenciando issue do Jira             | PASS   | Convenção `feat(SPK-XX): ...`obrigatória                          |
| Endpoints documentados no Swagger               | PASS   | FastAPI gera OpenAPI automaticamente via decorators                    |

---

## Project Structure

### Documentação do projeto

```
SDD/
├── constitution.md       # Princípios imutáveis do projeto
├── plan.md               # Este arquivo
├── data-model.md         # Esquema de banco (ER + descrição das tabelas)
└── contracts/
    ├── search-text.md    # Contrato POST /api/search/text
    ├── search-semantic.md # Contrato POST /api/search/semantic
    └── trigger-etl.md    # Contrato POST /internal/trigger-etl
```

### Código-fonte (raiz do repositório)

```
/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py           # Conexão asyncpg com Supabase
│   │   ├── routers/
│   │   │   ├── search.py         # /api/search/text e /api/search/semantic
│   │   │   └── internal.py       # /internal/trigger-etl
│   │   ├── services/
│   │   │   ├── text_search.py    # Lógica FTS com tsvector
│   │   │   ├── semantic_search.py # Lógica pgvector + cosseno
│   │   │   └── embeddings.py     # Geração via sentence-transformers
│   │   └── schemas.py            # Pydantic models (request/response)
│   ├── worker/
│   │   └── embeddings_worker.py  # Processa produções sem vetores
│   ├── migrations/               # SQL versionado (schema, triggers, RLS)
│   └── tests/
│       ├── unit/
│       └── integration/
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx              # Página de busca (UC-01, UC-02)
│   │   ├── producao/[id]/        # Detalhe da produção (UC-03)
│   │   └── pesquisador/[id]/     # Perfil do pesquisador (UC-04)
│   ├── components/
│   │   ├── SearchBar.tsx
│   │   ├── ProductionCard.tsx
│   │   ├── FilterPanel.tsx
│   │   └── Pagination.tsx
│   ├── lib/
│   │   └── api.ts                # Funções de chamada à FastAPI
│   └── tests/
│
├── etl/
│   ├── pipelines/                # Arquivos .hop do pipeline Apache Hop
│   ├── worker/
│   │   └── embeddings_worker.py  # Mesmo worker do backend, acionado pós-ETL
│   └── README.md                 # Instruções de instalação e execução
│
├── docker-compose.yml            # Ambiente de desenvolvimento local
├── .env.example                  # Variáveis de ambiente documentadas
└── README.md
```

**Structure Decision:** Web application (Option 2: backend + frontend separados), com diretório adicional `/etl/` para o pipeline Apache Hop e seu worker. O worker de embeddings é compartilhado entre o back-end (acionado via endpoint interno) e o ETL (acionado após carga direta pelo Engenheiro de Dados).

---

## Implementation

### Research

Decisões técnicas já resolvidas na especificação:

| Questão            | Decisão                         | Justificativa                                                 |
| ------------------- | -------------------------------- | ------------------------------------------------------------- |
| Modelo de embedding | `all-MiniLM-L6-v2`(local)      | Sem custo, 384 dimensões, bom trade-off qualidade/velocidade |
| Banco vetorial      | pgvector no Supabase             | Evita dependência externa; unifica relacional e vetorial     |
| Índice vetorial    | IVFFlat + vector_cosine_ops      | Performance com grande volume de produções                  |
| FTS engine          | tsvector nativo do PostgreSQL    | Sem dependência externa; índice GIN com suporte a booleanos |
| Orquestração ETL  | Apache Hop                       | Requisito do projeto; pipeline visual e auditável            |
| Enriquecimento      | CrossRef + OpenAlex + Qualis CSV | Fontes oficiais; CrossRef e OpenAlex são APIs abertas        |
| Auth                | Supabase Auth                    | Já integrado ao banco; apenas para Admin                     |

---

## Complexity Tracking

> Preenchido apenas para justificar desvios da constitution.

| Desvio                                                             | Por que é necessário                                                                          | Alternativa mais simples rejeitada porque                                              |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Worker de embeddings compartilhado entre `/backend`e `/etl`    | O Admin aciona via endpoint web; o Engenheiro de Dados aciona direto via Hop                    | Duplicar o worker geraria divergência de modelos e comportamento                      |
| Diretório `/etl/`adicional além de `backend/`e `frontend/` | Apache Hop é uma ferramenta externa que precisa de pipeline files (`.hop`) e README próprio | Mesclar com o backend misturaria responsabilidades incompatíveis (Python vs Java/Hop) |
