# SPARK — Memory / Context Keeper

Arquivo de estado da implementação. Atualizado a cada sprint para que qualquer agente possa continuar de onde o anterior parou.

---

## Estado atual: Sprint II em andamento

**Data:** 2026-05-23

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

### Sprint II — SPK-11 (código completo, validação pendente)

**SPK-36 — Ambiente Docker (CONCLUÍDO)**
- `docker-compose.yml` — PostgreSQL 15 + pgvector via imagem `pgvector/pgvector:pg15`
- `backend/migrations/01_schema_local.sql` — Schema local sem dependência de `auth.users` do Supabase; inclui tabelas `pesquisadores`, `producoes`, `vetores`, `etl_logs` com constraints, triggers (tsvector) e índices (GIN, IVFFlat)
- `.env.example` — variáveis documentadas: `POSTGRES_*`, `DATABASE_URL`, `XML_DIR`, `SUPABASE_*`

**SPK-37 — Pipeline Apache Hop: Extração e Transformação (CONCLUÍDO)**
- `etl/pipelines/lattes_pesquisadores.hpl` — Lista XMLs via `GetFileNames`, extrai dados do pesquisador via `GetDataFromXML` (loop `/CURRICULO-VITAE`, encoding ISO-8859-1), UPSERT via `ExecSQL`. Error handling redireciona arquivos problemáticos para `WriteToLog` sem interromper o batch.
- `etl/pipelines/lattes_producoes.hpl` — 4 fluxos paralelos (artigos, eventos, livros, capítulos), cada um com `GetFileNames` + `GetDataFromXML`. Unificados via `AppendedStreams`, normalizados via `ScriptValuesMod` (ISSN com hífen na posição 4, título sem caracteres de controle), lookup de `pesquisador_id` via `DBLookup`, UPSERT via `ExecSQL` com COALESCE.
- `etl/workflows/spark_etl.hwf` — Workflow que orquestra: 1) pesquisadores, 2) produções, 3) log em `etl_logs`. Ramo de falha registra `status='erro'`.

**SPK-38 — UPSERT e validação (CONCLUÍDO — código pronto, execução pendente)**
- UPSERT pesquisadores: `ON CONFLICT (lattes_id) DO UPDATE SET ...`
- UPSERT produções: `ON CONFLICT (pesquisador_id, titulo, ano_publicacao) DO UPDATE SET doi=COALESCE(...), resumo=COALESCE(...), qualis=COALESCE(...), jcr=COALESCE(...)` — preserva campos já enriquecidos em reprocessamentos

**SPK-39 — README, scripts e commit (CONCLUÍDO)**
- `etl/README.md` — instruções completas com sintaxe PowerShell e bash
- `etl/scripts/setup.ps1` — setup sem GUI: criptografa senha via `hop-encrypt.bat`, grava `spark_db.json` no formato correto do Hop 2.x, registra projeto via `hop-conf.bat`
- `etl/scripts/run-etl.ps1` — executa `spark_etl.hwf` via `hop-run.bat --project=spark --runconfig=local`

---

## Ambiente Apache Hop detectado

O Hop 2.15.0 está instalado em `C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop`.

- Java: `D:\jdk-21.0.9`
- Já existe um projeto `Lattes` registrado no Hop apontando para `config/projects/lattes/` (banco `BD_PESQUISADOR` na porta 5437 — projeto diferente do SPARK)
- O projeto SPARK deve ser registrado com nome `spark` apontando para `etl/`

**Comandos CLI relevantes:**
```powershell
# Setup único (criptografa senha, registra projeto):
cd etl\ && .\scripts\setup.ps1

# Execução do ETL:
.\scripts\run-etl.ps1

# Manualmente via hop-run.bat:
cmd /c """C:\...\hop-run.bat"" --project=spark --runconfig=local --file=""etl\workflows\spark_etl.hwf"" ""--parameters=XML_DIR=..."""
```

---

## Formato correto do spark_db.json (Hop 2.x)

O formato detectado na instalação local (Lattes.json) é **aninhado** — diferente do formato flat que estava no template inicial. O correto é:

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

A senha deve ser criptografada com `hop-encrypt.bat -hop <senha>` — não pode ser plain text nem variável de ambiente diretamente nesse campo.

---

## Estrutura de arquivos ETL relevante

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
│   ├── setup.ps1                  # Setup único — sem GUI
│   └── run-etl.ps1                # Execução do ETL — sem GUI
├── project-config.json            # Config do projeto no formato Hop 2.x
├── hop-config.json                # Legado (pode ser ignorado)
└── README.md
```

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
| Executar `setup.ps1` e `run-etl.ps1` | Validar com os 8 XMLs de `data/xml/` |
| Confirmar que `hop-run.bat --project=spark` funciona após o `setup.ps1` | Pode precisar ajustar caminhos no `project-config.json` |
| Renomear spec após Sprint Review | `spk11_spec.md` → `spk11_spec_CONCLUIDA.md` |

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

- **Dois pipelines separados** (pesquisadores → produções): UPSERT de produções faz lookup de `pesquisador_id`, que só existe depois do UPSERT de pesquisadores
- **4 GetFileNames separados** (um por tipo de produção): cada fluxo é independente e mais simples de depurar que fan-out de um único source
- **lattes_id extraído com XPath absoluto** (`/CURRICULO-VITAE/@NUMERO-IDENTIFICADOR`) mesmo dentro de loops de sub-elementos
- **Encoding ISO-8859-1** no `GetDataFromXML` — padrão CNPq; dados ficam corrompidos se lidos como UTF-8
- **Senha criptografada** no `spark_db.json` via `hop-encrypt.bat -hop` — Hop 2.x não aceita plain text ou variável de ambiente no campo `password` do formato JSON aninhado

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
