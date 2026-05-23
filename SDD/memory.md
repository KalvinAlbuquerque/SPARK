# SPARK — Memory / Context Keeper

Arquivo de estado da implementação. Atualizado a cada sprint para que qualquer agente possa continuar de onde o anterior parou.

---

## Estado atual: Sprint II em andamento

**Data:** 2026-05-22

---

## O que já foi implementado

### Sprint I (concluída)

| Artefato | Arquivo | Observações |
|----------|---------|-------------|
| Diagrama ER | `documentation/SPK-79_diagrama_er.puml` | Gerado com PlantUML |
| DDL Supabase | `documentation/SPK-79_ddl.sql` | Schema completo com RLS, triggers, pgvector |
| Diagrama de arquitetura | `documentation/SPK-73_arquitetura.puml` | Arquitetura de componentes |
| Casos de uso | `documentation/SPK-72_casos_de_uso.puml` | UC-01 a UC-05 |
| Imagens renderizadas | `documentation/*.png` | ER, arquitetura, casos de uso |

### Sprint II — SPK-11 (em andamento)

**SPK-36 — Ambiente Docker (CONCLUÍDO)**
- `docker-compose.yml` — PostgreSQL 15 + pgvector via imagem `pgvector/pgvector:pg15`
- `backend/migrations/01_schema_local.sql` — Schema local sem dependência de `auth.users` do Supabase; inclui tabelas `pesquisadores`, `producoes`, `vetores`, `etl_logs` com constraints, triggers (tsvector) e índices (GIN, IVFFlat)
- `.env.example` — variáveis documentadas incluindo `POSTGRES_*`, `DATABASE_URL`, `XML_DIR`, `SUPABASE_*`

**SPK-37 — Pipeline Apache Hop: Extração e Transformação (CONCLUÍDO)**
- `etl/pipelines/lattes_pesquisadores.hpl` — Pipeline que lista XMLs via `GetFileNames`, extrai dados do pesquisador via `GetDataFromXML` (loop `/CURRICULO-VITAE`, encoding ISO-8859-1), e faz UPSERT via `ExecSQL`. Error handling redireciona arquivos problemáticos para `WriteToLog` sem interromper o batch.
- `etl/pipelines/lattes_producoes.hpl` — Pipeline com 4 fluxos paralelos (artigos, eventos, livros, capítulos), cada um com seu próprio `GetFileNames` + `GetDataFromXML`. Os 4 fluxos são unidos via `AppendedStreams`, normalizados via `ScriptValuesMod` (ISSN com hífen, título sem caracteres de controle), com lookup de `pesquisador_id` via `DBLookup` e UPSERT via `ExecSQL` com COALESCE.
- `etl/metadata/rdbms/spark_db.json` — Template de conexão PostgreSQL usando variáveis de ambiente (`${POSTGRES_HOST}`, etc.)
- `etl/config/spark-env.json` — Template de ambiente Hop com variáveis pré-configuradas
- `etl/hop-config.json` — Configuração do projeto Hop

**SPK-38 — UPSERT e validação (CONCLUÍDO — código pronto, testes pendentes)**
- UPSERT de pesquisadores: `ON CONFLICT (lattes_id) DO UPDATE SET ...`
- UPSERT de produções: `ON CONFLICT (pesquisador_id, titulo, ano_publicacao) DO UPDATE SET doi=COALESCE(...), resumo=COALESCE(...), qualis=COALESCE(...), jcr=COALESCE(...)` — preserva campos enriquecidos
- Validação real com os XMLs em `data/xml/` (8 currículos disponíveis) ainda precisa ser executada com o Apache Hop instalado

**SPK-39 — README e commit (PARCIALMENTE CONCLUÍDO)**
- `etl/README.md` — instruções completas: pré-requisitos, configuração Docker, preparação dos XMLs, configuração da conexão Hop, execução via CLI e GUI, verificação de resultados, reprocessamento

---

## Arquivos XPath confirmados (validados nos XMLs reais)

Os XPaths foram confirmados analisando os arquivos em `data/xml/`:

| Tipo | Loop XPath | Título | Ano | DOI | Veículo | ISSN |
|------|-----------|--------|-----|-----|---------|------|
| ARTIGO | `.//ARTIGO-PUBLICADO` | `DADOS-BASICOS-DO-ARTIGO/@TITULO-DO-ARTIGO` | `DADOS-BASICOS-DO-ARTIGO/@ANO-DO-ARTIGO` | `DADOS-BASICOS-DO-ARTIGO/@DOI` | `DETALHAMENTO-DO-ARTIGO/@TITULO-DO-PERIODICO-OU-REVISTA` | `DETALHAMENTO-DO-ARTIGO/@ISSN` |
| EVENTO | `.//TRABALHO-EM-EVENTOS` | `DADOS-BASICOS-DO-TRABALHO/@TITULO-DO-TRABALHO` | `DADOS-BASICOS-DO-TRABALHO/@ANO-DO-TRABALHO` | `DADOS-BASICOS-DO-TRABALHO/@DOI` | `DETALHAMENTO-DO-TRABALHO/@NOME-DO-EVENTO` | (sem campo) |
| LIVRO | `.//LIVRO-PUBLICADO-OU-ORGANIZADO` | `DADOS-BASICOS-DO-LIVRO/@TITULO-DO-LIVRO` | `DADOS-BASICOS-DO-LIVRO/@ANO` | `DADOS-BASICOS-DO-LIVRO/@DOI` | `DADOS-BASICOS-DO-LIVRO/@TITULO-DO-LIVRO` | (sem campo) |
| CAPITULO | `.//CAPITULO-DE-LIVRO-PUBLICADO` | `DADOS-BASICOS-DO-CAPITULO/@TITULO-DO-CAPITULO-DO-LIVRO` | `DADOS-BASICOS-DO-CAPITULO/@ANO` | `DADOS-BASICOS-DO-CAPITULO/@DOI` | `DETALHAMENTO-DO-CAPITULO/@TITULO-DO-LIVRO` | (sem campo) |

`lattes_id` extraído em todos com XPath absoluto: `/CURRICULO-VITAE/@NUMERO-IDENTIFICADOR`

---

## O que falta fazer

### Sprint II — pendente

| Tarefa | Observação |
|--------|-----------|
| Executar pipeline com Apache Hop instalado | Validar com os 8 XMLs de `data/xml/` |
| Ajuste fino do hop-config.json | Pode precisar de ajuste de `PROJECT_HOME` para o ambiente específico |
| Commit no formato `feat(SPK-11): ...` | Fazer após validação |
| Atualizar spec com `_CONCLUIDA` | Renomear `spk11_spec.md` → `spk11_spec_CONCLUIDA.md` após Sprint Review |

### Próximas sprints

| Fase | Descrição |
|------|-----------|
| Fase 3 | Enriquecimento: Qualis CAPES (CSV Sucupira), CrossRef (DOI/resumo), OpenAlex (JCR) |
| Fase 5 | Atualização de métricas bibliométricas (`total_producoes`, `indice_h`, `total_a1_a2`) |
| Fase 6 | Worker de embeddings (`all-MiniLM-L6-v2`) para busca semântica |
| API | Endpoints FastAPI: `POST /api/search/text`, `POST /api/search/semantic`, `POST /internal/trigger-etl` |
| Frontend | Next.js 14 com busca, cards de produção, filtros sem reload |

---

## Decisões técnicas importantes

- **Dois pipelines separados** (pesquisadores → produções) em vez de um único: necessário porque o UPSERT de produções faz lookup de `pesquisador_id` que só existe após o UPSERT de pesquisadores
- **4 GetFileNames separados** (um por tipo de produção) em vez de um com fan-out: mais simples de manter; cada fluxo é independente
- **lattes_id extraído com XPath absoluto** (`/CURRICULO-VITAE/@NUMERO-IDENTIFICADOR`) mesmo dentro de loops de sub-elementos
- **Encoding ISO-8859-1** configurado no `GetDataFromXML` — padrão do CNPq; os dados ficam corrompidos se lidos como UTF-8

---

## Dados de teste disponíveis

`data/xml/` contém 8 currículos Lattes reais da UNEB com `DEPARTAMENTO="DCET"` e `CAMPUS="Campus I"` já preenchidos:
- 1608472474770322.xml
- 1966167015825708.xml
- 3633682231940138.xml
- 4436012961948689.xml
- 4940207771377721.xml
- 5601958689947032.xml
- 6716225567627323.xml
- 7401907691814937.xml
