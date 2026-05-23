# Proof of Work — SPK-13: Enriquecimento CrossRef e OpenAlex

**Data:** 2026-05-23  
**Pipelines:** `crossref_enriquecimento.hpl` · `openalex_enriquecimento.hpl`  
**Workflow:** `spark_etl.hwf` (etapas Pipeline CrossRef e Pipeline OpenAlex)

---

## Objetivo

Demonstrar que o SPK-13 atende aos critérios de aceite da spec:

| Critério | Meta |
|----------|------|
| `doi` preenchido após enriquecimento | ≥ 90% dos artigos |
| `resumo` preenchido | ≥ 50% dos artigos |
| `jcr` preenchido | ≥ 70% dos artigos |
| Pipeline não interrompido por falha de API | 100% |
| Idempotência | 2 execuções → mesmo resultado |

---

## Estado antes do enriquecimento (pós-carga Lattes)

Após `lattes_producoes.hpl`, os campos de enriquecimento estavam assim:

| Campo | Preenchido | % |
|-------|-----------|---|
| `doi` | 216 / 247 | 87.4% — vindo do XML Lattes |
| `resumo` | 0 / 247 | 0% — XML não contém abstract |
| `jcr` | 0 / 247 | 0% — não existe no XML |

---

## Execução

### Comando

```powershell
cd etl\scripts
.\run-etl.ps1 -XmlDir "C:\...\data\xml"
```

O script carrega `.env` automaticamente (inclui `ETL_EMAIL` e `OPENALEX_APIKEY`) e passa
os valores ao `hop-run` via `--parameters`.

### Saída do terminal (execução de referência — 2026-05-23 16:13)

```
=== SPARK ETL ===================================================
ETL Email: glendasantana2099@gmail.com
OpenAlex:  (configurado)
=================================================================
Arquivos XML encontrados: 8
Iniciando workflow...
=== ETL concluido em 121s ===========================
```

Pipeline OpenAlex — stats do Hop:

```
Ler ISSNs.0          - Finished processing (I=145, O=0, R=0,   W=145, U=0, E=0)
Unico por ISSN.0     - Finished processing (I=0,   O=0, R=145, W=145, U=0, E=0)
HTTP OpenAlex.0      - Finished processing (I=0,   O=0, R=145, W=145, U=0, E=0)
Extrair JCR.0        - Finished processing (I=0,   O=0, R=145, W=145, U=0, E=0)
Filtrar JCR.0        - Finished processing (I=0,   O=0, R=145, W=145, U=0, E=0)
Log sem_match_jcr.0  - Finished processing (I=0,   O=0, R=4,   W=4,   U=0, E=0)
UPSERT JCR.0         - Finished processing (I=0,   O=0, R=141, W=141, U=0, E=0)
```

- **145 ISSNs únicos** processados (deduplicação funcionou — 247 artigos → 145 chamadas)
- **141 ISSNs** com `2yr_mean_citedness` → UPSERT executado
- **4 ISSNs** sem correspondência no OpenAlex → logados, `jcr` = NULL

---

## Resultado após enriquecimento

```sql
SELECT
  COUNT(*) FILTER (WHERE doi IS NOT NULL)    AS com_doi,
  COUNT(*) FILTER (WHERE resumo IS NOT NULL) AS com_resumo,
  COUNT(*) FILTER (WHERE jcr IS NOT NULL)    AS com_jcr,
  COUNT(*)                                   AS total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE doi IS NOT NULL)    / COUNT(*), 1) AS pct_doi,
  ROUND(100.0 * COUNT(*) FILTER (WHERE resumo IS NOT NULL) / COUNT(*), 1) AS pct_resumo,
  ROUND(100.0 * COUNT(*) FILTER (WHERE jcr IS NOT NULL)    / COUNT(*), 1) AS pct_jcr
FROM producoes WHERE tipo_producao = 'ARTIGO';
```

| com_doi | com_resumo | com_jcr | total | pct_doi | pct_resumo | pct_jcr |
|---------|-----------|---------|-------|---------|-----------|---------|
| 226 | 137 | 243 | 247 | **91.5%** | **55.5%** | **98.4%** |

### Critérios de aceite

| Critério | Meta | Resultado | Status |
|----------|------|-----------|--------|
| `doi` ≥ 90% | 90% | **91.5%** | ✓ |
| `resumo` ≥ 50% | 50% | **55.5%** | ✓ |
| `jcr` ≥ 70% | 70% | **98.4%** | ✓ |

---

## Detalhamento por ramo

### CrossRef — Ramo A (com DOI)

| Situação | Qtd |
|----------|-----|
| Artigos com DOI no XML | 216 |
| Com abstract retornado → `resumo` preenchido | 137 |
| Sem abstract na CrossRef → `resumo` = NULL | 79 |

Os 79 sem abstract são artigos cujos publishers não submetem abstracts à CrossRef
(periódicos brasileiros de menor porte, em sua maioria). Comportamento esperado.

### CrossRef — Ramo B (busca por título)

| Situação | Qtd |
|----------|-----|
| Artigos sem DOI no XML | 31 |
| Score > 70 (DOI aceito) | 10 |
| Score ≤ 70 (descartado → `sem_match_doi`) | 21 |

10 artigos que não tinham DOI no XML ganharam DOI via busca por título.

### OpenAlex — JCR por ISSN

| Situação | Qtd |
|----------|-----|
| ISSNs únicos processados | 145 |
| Com `2yr_mean_citedness` | 141 |
| Sem correspondência (`sem_match_jcr`) | 4 |

Um UPDATE por ISSN atualiza todos os artigos daquele periódico de uma vez.
Exemplo: ISSN `0048-9697` (Science of the Total Environment, JCR = 9.951) atualizou 4 artigos
com uma única chamada à API.

### Distribuição do JCR preenchido

| Faixa JCR | Artigos |
|-----------|---------|
| ≥ 5.0 (alto impacto) | 16 |
| 2.0 – 4.9 | 82 |
| 1.0 – 1.9 | 29 |
| 0.1 – 0.9 | 99 |
| 0.0 | 17 |
| NULL (sem ISSN indexado) | 4 |

Média JCR do corpus: **1.838**

### Exemplos de artigos com resumo e JCR preenchidos

| DOI | JCR | Trecho do resumo |
|-----|-----|-----------------|
| 10.2807/1560-7917.es.2017.22.24.30552 | 7.364 | We describe a series of 15 Haff disease cases from an outbreak in Salvador… |
| 10.3389/fmicb.2021.632695 | 4.627 | Co-infection between the human T-cell lymphotropic virus (HTLV) and th… |
| 10.1038/s41598-021-91306-z | 4.308 | We investigated the relation between the spread, time scale, and spatial… |

---

## Preservação de dados (COALESCE)

O UPSERT usa `COALESCE(novo, existente)` — nunca sobrescreve um valor já preenchido com NULL.

```sql
-- CrossRef
UPDATE producoes SET
  doi    = COALESCE(?, doi),
  resumo = COALESCE(?, resumo)
WHERE id = ?;

-- OpenAlex
UPDATE producoes SET
  jcr = COALESCE(?, jcr)
WHERE issn = ?;
```

Evidência: após a execução, nenhum artigo que já tinha DOI no XML perdeu o valor.

---

## Idempotência

Duas execuções consecutivas produzem o mesmo resultado:

| Métrica | Run 1 (16:13) | Run 2 (17:07) |
|---------|--------------|--------------|
| `com_resumo` | 137 | 137 |
| `com_jcr` | 243 | 243 |
| `média jcr` | 1.8380 | 1.8380 |

---

## Falhas de API — comportamento

Os 4 ISSNs sem match no OpenAlex foram logados via `WriteToLog` e receberam `jcr = NULL`.
O pipeline continuou sem interrupção — `E=0` em todos os transforms.

Logs registrados em `etl_logs` com `detalhes` JSONB incluindo `sem_match_jcr`.

---

## Artefatos entregues

| Arquivo | Descrição |
|---------|-----------|
| `etl/pipelines/crossref_enriquecimento.hpl` | Pipeline CrossRef: DOI + resumo |
| `etl/pipelines/openalex_enriquecimento.hpl` | Pipeline OpenAlex: JCR por ISSN |
| `etl/workflows/spark_etl.hwf` | Workflow atualizado com os dois novos pipelines |
| `etl/scripts/run-etl.ps1` | Script atualizado com carregamento de `.env` e parâmetros `ETL_EMAIL`/`OPENALEX_APIKEY` |
| `etl/scripts/run-etl.sh` | Equivalente para Linux/macOS |
| `.env.example` | Atualizado com `ETL_EMAIL` e `OPENALEX_APIKEY` |
| `etl/README.md` | Atualizado: seção de variáveis de ambiente, instrução de API key OpenAlex |
| `SDD/sprint_2/spk13_spec_CONCLUIDA.md` | Spec renomeada |
