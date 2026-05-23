# SPARK — Memory / Context Keeper

Arquivo de estado da implementação. Atualizado a cada sprint para que qualquer agente possa continuar de onde o anterior parou.

---

## Estado atual: Sprint II — SPK-11 + SPK-12 + SPK-13 CONCLUÍDAS

**Data última atualização:** 2026-05-23

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

---

### Sprint II — SPK-11 + SPK-12 (CONCLUÍDAS e VALIDADAS ✓)

**Spec:** `SDD/sprint_2/spk11_spec_CONCLUIDA.md`

**SPK-36 — Ambiente Docker (CONCLUÍDO)**
- `docker-compose.yml` — PostgreSQL 15 + pgvector via imagem `pgvector/pgvector:pg15`
- `backend/migrations/01_schema_local.sql` — Schema local sem dependência de `auth.users` do Supabase; inclui tabelas `pesquisadores`, `producoes`, `vetores`, `etl_logs` com constraints, triggers (tsvector) e índices (GIN, IVFFlat)
- `.env.example` — variáveis documentadas: `POSTGRES_*`, `DATABASE_URL`, `XML_DIR`, `SUPABASE_*`
- Container em execução: `spark-db-1` (healthcheck OK)

**SPK-37 — Pipeline Apache Hop: Extração e Transformação (CONCLUÍDO e VALIDADO)**
- `etl/pipelines/lattes_pesquisadores.hpl` — `GetFileNames` → `GetXmlData` (loop `/CURRICULO-VITAE`) → `ExecSQL` UPSERT. Error handling via `transform_error_handling` redireciona arquivos com falha para `WriteToLog` sem interromper o batch.
- `etl/pipelines/lattes_producoes.hpl` — 4 fluxos paralelos (artigos, eventos, livros, capítulos), cada um com `GetFileNames` + `GetXmlData`. Normalizados via `ScriptValueMod` (ISSN com hífen, título sem caracteres de controle), filtro de linhas sem match (`FilterRows`), lookup de `pesquisador_id` via `DBLookup`, UPSERT via `ExecSQL` com COALESCE.
- `etl/workflows/spark_etl.hwf` — Workflow que orquestra: 1) pesquisadores, 2) produções, 3) log em `etl_logs`. Ramo de falha registra `status='erro'`.

**SPK-38 — UPSERT e validação (CONCLUÍDO — executado e validado)**
- UPSERT pesquisadores: `ON CONFLICT (lattes_id) DO UPDATE SET ...`
- UPSERT produções: `ON CONFLICT (pesquisador_id, titulo, ano_publicacao) DO UPDATE SET doi=COALESCE(...), resumo=COALESCE(...), qualis=COALESCE(...), jcr=COALESCE(...)` — preserva campos já enriquecidos em reprocessamentos
- **Idempotência confirmada:** 2 execuções consecutivas → mesmos 8 pesquisadores, 462 produções, sem duplicatas

---

### Sprint II — SPK-12 (CONCLUÍDA e VALIDADA ✓)

**Spec:** `SDD/sprint_2/spk12_spec_CONCLUIDA.md`

**Pipeline de enriquecimento Qualis CAPES**

- `etl/pipelines/qualis_enriquecimento.hpl` — Pipeline Apache Hop que:
  - Lê `data/qualis/qualis_capes.csv` (154.518 linhas, quadriênio 2017–2020)
  - Ramo A: `CSVInput` → `SortRows` (ISSN asc, Estrato asc) → `Unique` por ISSN → `StreamLookup` no fluxo de artigos
  - Ramo B (fallback): mesma estrutura mas por `Titulo` → `StreamLookup` por `nome_veiculo`
  - `FilterRows` roteia: match → `ExecSQL` UPSERT, sem match → `WriteToLog`
  - UPSERT: `UPDATE producoes SET qualis = COALESCE(?, qualis) WHERE id = ?`
  - **Idempotência confirmada:** 2 execuções consecutivas → mesmo resultado
- `etl/workflows/spark_etl.hwf` — Pipeline Qualis adicionado entre "Pipeline Producoes" e "Registrar sucesso"; parâmetro `QUALIS_CSV` adicionado
- `etl/scripts/run-etl.ps1` e `run-etl.sh` — Parâmetro `-QualisCSV` / `QUALIS_CSV` adicionado
- `data/qualis/qualis_capes.csv` — CSV gerado do XLSX da Plataforma Sucupira (31.350 ISSNs únicos)

**Resultado validado (2026-05-23):**

| Métrica | Resultado |
|---------|-----------|
| Taxa de match (ISSN + fallback nome) | **93.1%** (230/247 artigos) |
| Artigos sem correspondência | 17 (logados sem interromper o batch) |
| Idempotência | ✓ (2 runs consecutivos → mesmo resultado) |
| Estratos preenchidos | A1:64, A2:40, A3:21, A4:33, B1:27, B2:18, B3:2, B4:2, C:23 |

**Quirks descobertos no SPK-12:**

7. **Tipos de transform CSVInput no Hop 2.x**: O tipo correto é `CSVInput` (não `CsvInput`) e o tag de buffer é `<buffer_size>` (não `<bufferSize>`) — caso contrário: `NumberFormatException: Cannot parse null string` no init.
8. **UniqueRows no Hop 2.x**: O tipo correto é `Unique` (não `UniqueRows`) — confirmar via sample `unique-rows-basic.hpl`.
9. **Ordem alfabética dos estratos Qualis**: A1 < A2 < ... < B5 < C alfabeticamente = ordem de qualidade decrescente. Logo `SortRows` (ISSN asc, Estrato asc) + `UniqueRows` garante o melhor estrato por ISSN sem conversão numérica — elimina a necessidade de `ScriptValueMod`/`ScriptValues`.

**SPK-39 — README, scripts e commit (CONCLUÍDO)**
- `etl/README.md` — instruções completas com sintaxe PowerShell e bash
- `etl/scripts/setup.ps1` e `setup.sh` — setup sem GUI: criptografam senha via `hop-encrypt`, gravam `spark_db.json` no formato correto do Hop 2.x, registram projeto via `hop-conf`; suportam senha via variável de ambiente (`$env:POSTGRES_PASSWORD`), parâmetro ou prompt interativo
- `etl/scripts/run-etl.ps1` e `run-etl.sh` — executam `spark_etl.hwf` via `hop-run --project=spark --runconfig=local`

---

## Resultado da execução (dados validados em 2026-05-23)

### Pesquisadores carregados (8/8)

| lattes_id | nome_completo | depto | campus | resumo |
|-----------|---------------|-------|--------|--------|
| 7401907691814937 | Aloisio Santos Nascimento Filho | DCET | Campus I | preenchido |
| 6716225567627323 | Eduardo Manuel de Freitas Jorge | DCET | Campus I | preenchido |
| 1966167015825708 | Hugo Saba Pereira Cardoso | DCET | Campus I | preenchido |
| 1608472474770322 | José Garcia Vivas Miranda | DCET | Campus I | preenchido |
| 4436012961948689 | Maria Fernanda Rios Grassi | DCET | Campus I | preenchido |
| 4940207771377721 | Mayara Maria de Jesus Almeida | DCET | Campus I | preenchido |
| 3633682231940138 | Paulo Jorge Silveira Ferreira | DCET | Campus I | NULL (XML sem resumo) |
| 5601958689947032 | Raphael Silva do Rosário | DCET | Campus I | preenchido |

### Produções carregadas (462 total)

| Tipo | Qtd |
|------|-----|
| ARTIGO | 247 |
| EVENTO | 161 |
| CAPITULO | 40 |
| LIVRO | 14 |

> Paulo Jorge Silveira Ferreira tem 0 produções — o XML dele genuinamente não contém registros em `PRODUCAO-BIBLIOGRAFICA`.

---

## O que o ETL preenche e o que não preenche

### Tabela `pesquisadores`

| Coluna | ETL preenche? | Observação |
|--------|--------------|------------|
| `lattes_id` | Sim | Do XML |
| `nome_completo` | Sim | Do XML |
| `departamento` | Sim | Campo adicionado manualmente no XML |
| `campus` | Sim | Campo adicionado manualmente no XML |
| `resumo` | Sim (quando existe) | NULL se XML não tiver o campo |
| `data_atualizacao` | Sim | NOW() no UPSERT |
| `total_producoes` | **Não** (fica 0) | Métrica calculada — sprint futura |
| `indice_h` | **Não** (fica 0) | Métrica calculada — sprint futura |
| `total_a1_a2` | **Não** (fica 0) | Métrica calculada — sprint futura |

### Tabela `producoes`

| Coluna | ETL preenche? | Observação |
|--------|--------------|------------|
| `pesquisador_id` | Sim | Lookup por lattes_id |
| `titulo` | Sim | Do XML |
| `tipo_producao` | Sim | Constante por fluxo |
| `ano_publicacao` | Sim | Do XML |
| `nome_veiculo` | Sim | Periódico / evento / livro pai |
| `issn` | Sim (quando existe) | Do XML |
| `doi` | Sim (quando existe) | Do XML |
| `texto_busca` | Sim (automático) | Trigger do banco |
| `resumo` | **Sim** (SPK-13) | `crossref_enriquecimento.hpl` — cobertura parcial esperada (depende da CrossRef por editora) |
| `qualis` | **Sim** (SPK-12) | Pipeline `qualis_enriquecimento.hpl` — 93.1% dos artigos preenchidos |
| `jcr` | **Sim** (SPK-13) | `openalex_enriquecimento.hpl` — 1 chamada por ISSN único |

---

## Ambiente Apache Hop

- Versão: 2.15.0 instalada em `C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop`
- Java: `D:\jdk-21.0.9`
- Projeto registrado: `spark` apontando para `etl/`
- Conexão: `spark_db` (PostgreSQL localhost:5432, banco `spark`, user `spark`)
- Container Docker: `spark-db-1` (porta 5432)

**Comandos CLI:**
```powershell
# Setup único (criptografa senha, registra projeto):
$env:POSTGRES_PASSWORD = "spark123"
cd etl\; .\scripts\setup.ps1

# Execução do ETL:
.\scripts\run-etl.ps1
```

---

## Quirks do Apache Hop 2.15.0 descobertos

1. **`distribute=N` em copy mode**: Com `distribute=N` e um error handler configurado, o Hop em modo "copy" envia cada linha para TODOS os hops de saída (incluindo o error handler), não apenas para o hop principal. Isso faz com que o `Log Erro Parse` receba todas as linhas, mesmo sem erros reais (E=0). O UPSERT recebe igualmente todas as linhas e funciona corretamente — é um comportamento cosmético do log, não afeta os dados.

2. **Tipo correto dos transforms (SPK-11)**: `GetXmlData` (não `GetDataFromXML`), `Constant` (não `AddConstants`), `ScriptValueMod` (não `ScriptValuesMod`).
   **Tipos corretos (SPK-12)**: `CSVInput` (não `CsvInput`), `Unique` (não `UniqueRows`). Tag `<buffer_size>` (não `<bufferSize>`).

3. **`loopxpath` como tag direta**: `<loopxpath>/CURRICULO-VITAE</loopxpath>`, não dentro de `<loops><loop><path>`.

4. **`ExecSQL` com parâmetros**: Requer `<set_params>Y</set_params>` e cada argumento como `<argument><name>campo</name></argument>`.

5. **Senha no spark_db.json**: Deve ser criptografada com `hop-encrypt.bat -hop <senha>` — Hop 2.x não aceita plain text.

6. **Formato spark_db.json (Hop 2.x)**: Formato aninhado com chave `rdbms.POSTGRESQL`, não flat.

---

## Formato correto do spark_db.json (Hop 2.x)

```json
{
  "virtualPath": "",
  "rdbms": {
    "POSTGRESQL": {
      "databaseName": "spark",
      "pluginId": "POSTGRESQL",
      "accessType": 0,
      "hostname": "localhost",
      "password": "Encrypted <hash gerado pelo setup.ps1>",
      "pluginName": "PostgreSQL",
      "port": "5432",
      "attributes": { ... },
      "username": "spark"
    }
  },
  "name": "spark_db"
}
```

---

## Estrutura de arquivos ETL

```
etl/
├── pipelines/
│   ├── lattes_pesquisadores.hpl     # Extrai e carrega pesquisadores (SPK-11)
│   ├── lattes_producoes.hpl         # Extrai e carrega produções - 4 tipos (SPK-11)
│   ├── qualis_enriquecimento.hpl    # Enriquece qualis via planilha CAPES (SPK-12)
│   ├── crossref_enriquecimento.hpl  # Enriquece doi + resumo via CrossRef API (SPK-13)
│   └── openalex_enriquecimento.hpl  # Enriquece jcr via OpenAlex API por ISSN (SPK-13)
├── workflows/
│   └── spark_etl.hwf                # Orquestra os 5 pipelines + log etl_logs
├── metadata/
│   └── rdbms/
│       └── spark_db.json            # Conexão PostgreSQL (gerada pelo setup.ps1)
├── config/
│   └── spark-env.json               # Template de variáveis Hop (referência)
├── scripts/
│   ├── setup.ps1                    # Setup único — Windows
│   ├── setup.sh                     # Setup único — Linux/macOS
│   ├── run-etl.ps1                  # Execução do ETL — Windows (aceita -QualisCSV)
│   └── run-etl.sh                   # Execução do ETL — Linux/macOS (aceita $2 ou QUALIS_CSV)
├── docs/
│   └── upsert_proof_of_work.md      # Prova de idempotência do UPSERT
├── project-config.json              # Config do projeto no formato Hop 2.x
└── README.md
```

---

## XPaths validados nos XMLs reais

| Tipo | Loop XPath | Título | Ano | DOI | Veículo | ISSN |
|------|-----------|--------|-----|-----|---------|------|
| ARTIGO | `.//ARTIGO-PUBLICADO` | `DADOS-BASICOS-DO-ARTIGO/@TITULO-DO-ARTIGO` | `DADOS-BASICOS-DO-ARTIGO/@ANO-DO-ARTIGO` | `DADOS-BASICOS-DO-ARTIGO/@DOI` | `DETALHAMENTO-DO-ARTIGO/@TITULO-DO-PERIODICO-OU-REVISTA` | `DETALHAMENTO-DO-ARTIGO/@ISSN` |
| EVENTO | `.//TRABALHO-EM-EVENTOS` | `DADOS-BASICOS-DO-TRABALHO/@TITULO-DO-TRABALHO` | `DADOS-BASICOS-DO-TRABALHO/@ANO-DO-TRABALHO` | `DADOS-BASICOS-DO-TRABALHO/@DOI` | `DETALHAMENTO-DO-TRABALHO/@NOME-DO-EVENTO` | — |
| LIVRO | `.//LIVRO-PUBLICADO-OU-ORGANIZADO` | `DADOS-BASICOS-DO-LIVRO/@TITULO-DO-LIVRO` | `DADOS-BASICOS-DO-LIVRO/@ANO` | `DADOS-BASICOS-DO-LIVRO/@DOI` | `DADOS-BASICOS-DO-LIVRO/@TITULO-DO-LIVRO` | — |
| CAPITULO | `.//CAPITULO-DE-LIVRO-PUBLICADO` | `DADOS-BASICOS-DO-CAPITULO/@TITULO-DO-CAPITULO-DO-LIVRO` | `DADOS-BASICOS-DO-CAPITULO/@ANO` | `DADOS-BASICOS-DO-CAPITULO/@DOI` | `DETALHAMENTO-DO-CAPITULO/@TITULO-DO-LIVRO` | — |

`lattes_id` extraído em todos com XPath absoluto: `/CURRICULO-VITAE/@NUMERO-IDENTIFICADOR`

Pesquisador (loop raiz): `/CURRICULO-VITAE` → `@NUMERO-IDENTIFICADOR`, `DADOS-GERAIS/@NOME-COMPLETO`, `DADOS-GERAIS/@DEPARTAMENTO`, `DADOS-GERAIS/@CAMPUS`, `DADOS-GERAIS/RESUMO-CV/@TEXTO-RESUMO-CV-RH`

---

## Dados de teste

`data/xml/` contém 8 currículos Lattes reais da UNEB com `DEPARTAMENTO="DCET"` e `CAMPUS="Campus I"` já preenchidos:
- 1608472474770322.xml — José Garcia Vivas Miranda
- 1966167015825708.xml — Hugo Saba Pereira Cardoso
- 3633682231940138.xml — Paulo Jorge Silveira Ferreira (sem produções no XML)
- 4436012961948689.xml — Maria Fernanda Rios Grassi
- 4940207771377721.xml — Mayara Maria de Jesus Almeida
- 5601958689947032.xml — Raphael Silva do Rosário
- 6716225567627323.xml — Eduardo Manuel de Freitas Jorge
- 7401907691814937.xml — Aloisio Santos Nascimento Filho

---

## O que falta fazer (próximas sprints)

| Fase | Descrição | Status |
|------|-----------|--------|
| Fase 3 — SPK-12 | Enriquecimento Qualis CAPES | **CONCLUÍDO** (93.1% match) |
| Fase 3 — SPK-13 | Enriquecimento CrossRef (DOI + resumo) + OpenAlex (JCR) | **CONCLUÍDO** — spec em `SDD/sprint_2/spk13_spec_CONCLUIDA.md` |
| SPK-14 | Spike: avaliação de modelos de embedding (Sentence-Transformers vs OpenAI) | Pendente |
| Fase 5 | Atualização de métricas bibliométricas (`total_producoes`, `indice_h`, `total_a1_a2`) via SQL por pesquisador processado | Pendente |
| Fase 6 | Worker de embeddings (`all-MiniLM-L6-v2`) acionado via `POST /internal/trigger-embeddings` | Pendente |
| API | Endpoints FastAPI: `POST /api/search/text`, `POST /api/search/semantic`, `POST /internal/trigger-etl` | Pendente |
| Frontend | Next.js 14 com busca, cards de produção, filtros sem reload | Pendente |

---

## Roadmap completo do ETL (RoadMap_para_ETL.pdf v1.2)

O pipeline executa **6 fases em sequência**:

| Fase | Descrição | Sprint / Issue |
|------|-----------|---------------|
| Fase 1 | Extração dos XMLs Lattes | **CONCLUÍDO** (SPK-11) |
| Fase 2 | Transformação e normalização (ISSN, títulos, UPSERT) | **CONCLUÍDO** (SPK-11) |
| Fase 3a | Enriquecimento Qualis (CSV local, lookup por ISSN + fallback por nome) | **CONCLUÍDO** (SPK-12) |
| Fase 3b | Enriquecimento CrossRef (DOI + abstract) + OpenAlex (JCR) — ambos no SPK-13 | **CONCLUÍDO** (SPK-13) |
| Fase 4 | Carga no Supabase (UPSERT com COALESCE) | **CONCLUÍDO** (SPK-11) |
| Fase 5 | Atualização de métricas por pesquisador (`total_producoes`, `indice_h`, `total_a1_a2`) | Pendente |
| Fase 6 | Acionamento do Worker de embeddings (`all-MiniLM-L6-v2`) via HTTP | Pendente |

**Endpoint interno:** `POST /internal/trigger-etl` — executa as 6 fases sem Apache Hop (para upload pelo Admin via interface web).

### SPK-13 — CONCLUÍDO (CrossRef + OpenAlex)

**crossref_enriquecimento.hpl** (Fase 3b — subetapa 5.2):
- Scope: apenas `tipo_producao = 'ARTIGO'`
- Ramo A (com DOI): `GET /works/{doi}?select=DOI,title,abstract` → extrai abstract
- Ramo B (sem DOI): `GET /works?query.bibliographic={titulo}&rows=1` → aceita DOI apenas se `score > 70`
- Header obrigatório: `User-Agent: SPARK-ETL/1.0 (mailto:${ETL_EMAIL})`
- Variável de ambiente: `ETL_EMAIL` no `.env`
- Tags HTML removidas do abstract via regex `/<[^>]+>/g`
- UPSERT: `UPDATE producoes SET doi = COALESCE(?,doi), resumo = COALESCE(?,resumo) WHERE id = ?`
- Logs: `sem_match_doi`, `sem_resumo`

**openalex_enriquecimento.hpl** (Fase 3b — subetapa 5.3):
- Scope: todos os registros com ISSN preenchido
- Deduplicação: `SortRows` + `Unique` por ISSN antes das chamadas HTTP
- Endpoint: `GET /sources/issn:{issn}?select=issn_l,display_name,2yr_mean_citedness&api_key={OPENALEX_APIKEY}`
- Campo: `2yr_mean_citedness` → `producoes.jcr`
- Um UPDATE por ISSN atualiza TODOS os artigos com aquele ISSN
- Variável de ambiente: `OPENALEX_APIKEY` no `.env` (API key gratuita — openalex.org)
- HTTP 404 ou campo null → NULL (não é falha)
- UPSERT: `UPDATE producoes SET jcr = COALESCE(?,jcr) WHERE issn = ?`
- Log: `sem_match_jcr`

**Integração no workflow:**
- Fluxo: Qualis → Registrar sem match Qualis → CrossRef → OpenAlex → Registrar sem match CrossRef OpenAlex → Registrar sucesso
- Parâmetros novos no workflow: `ETL_EMAIL`, `OPENALEX_APIKEY`
- Scripts `run-etl.ps1` e `run-etl.sh` carregam `.env` automaticamente e passam essas vars ao hop-run

**Quirks descobertos no SPK-13:**
10. **`SelectValues` antes de `AppendStreams`**: Necessário normalizar o schema dos dois ramos (com DOI e sem DOI) para os mesmos campos (`id`, `doi_novo`, `resumo_novo`) antes de reunir — AppendStreams usa o schema do head stream como base.
11. **`getVariable()` no JavaScript Hop**: Para acessar parâmetros de pipeline dentro de `ScriptValueMod`, usar `parent.getVariable("ETL_EMAIL", "default")`.
12. **OpenAlex API key obrigatória desde 13/02/2026**: Plano gratuito inclui 100k créditos/dia; singletons (`/sources/issn:xxx`) custam 0 créditos.

### Fase 5 — Métricas bibliométricas

SQL executado uma vez por pesquisador processado na execução corrente:
```sql
UPDATE pesquisadores SET
  total_producoes = (SELECT COUNT(*) FROM producoes WHERE pesquisador_id = ?),
  total_a1_a2 = (SELECT COUNT(*) FROM producoes WHERE pesquisador_id = ? AND qualis IN ('A1','A2')),
  indice_h = (
    SELECT COUNT(*) FROM (
      SELECT jcr, ROW_NUMBER() OVER (ORDER BY jcr DESC) AS pos
      FROM producoes WHERE pesquisador_id = ? AND jcr IS NOT NULL
    ) ranked WHERE jcr >= pos
  )
WHERE id = ?;
```
Produções sem JCR são excluídas do cálculo do `indice_h`. `total_producoes` conta todos os tipos.
