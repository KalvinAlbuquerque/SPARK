# SPARK — Memory / Context Keeper

Arquivo de estado da implementação. Atualizado a cada sprint para que qualquer agente possa continuar de onde o anterior parou.

---

## Estado atual: Sprint II CONCLUÍDA

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

### Sprint II — SPK-11 (CONCLUÍDA e VALIDADA ✓)

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
| `resumo` | **Não** (fica NULL) | `RESUMO-DA-PRODUCAO` não extraído na SPK-11 |
| `qualis` | **Não** (fica NULL) | Enriquecimento externo — sprint futura |
| `jcr` | **Não** (fica NULL) | Enriquecimento externo — sprint futura |

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

2. **Tipo correto dos transforms**: `GetXmlData` (não `GetDataFromXML`), `Constant` (não `AddConstants`), `ScriptValueMod` (não `ScriptValuesMod`).

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
│   ├── lattes_pesquisadores.hpl   # Extrai e carrega pesquisadores
│   └── lattes_producoes.hpl       # Extrai e carrega produções (4 tipos)
├── workflows/
│   └── spark_etl.hwf              # Orquestra ambos + log etl_logs
├── metadata/
│   └── rdbms/
│       └── spark_db.json          # Conexão PostgreSQL (gerada pelo setup.ps1)
├── config/
│   └── spark-env.json             # Template de variáveis Hop (referência)
├── scripts/
│   ├── setup.ps1                  # Setup único — Windows
│   ├── setup.sh                   # Setup único — Linux/macOS
│   ├── run-etl.ps1                # Execução do ETL — Windows
│   └── run-etl.sh                 # Execução do ETL — Linux/macOS
├── project-config.json            # Config do projeto no formato Hop 2.x
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

| Fase | Descrição | Prioridade |
|------|-----------|-----------|
| Fase 3 | Enriquecimento: Qualis CAPES (CSV Sucupira), CrossRef (DOI → resumo), OpenAlex (JCR) | Alta |
| Fase 5 | Atualização de métricas bibliométricas (`total_producoes`, `indice_h`, `total_a1_a2`) | Alta |
| Fase 6 | Worker de embeddings (`all-MiniLM-L6-v2`) para busca semântica | Média |
| API | Endpoints FastAPI: `POST /api/search/text`, `POST /api/search/semantic`, `POST /internal/trigger-etl` | Alta |
| Frontend | Next.js 14 com busca, cards de produção, filtros sem reload | Média |
| ETL futuro | Extrair `resumo` das produções (`RESUMO-DA-PRODUCAO`) se necessário | Baixa |
