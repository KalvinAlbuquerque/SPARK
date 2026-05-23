# SPK-13 — Enriquecimento CrossRef e OpenAlex: DOI, Resumo e JCR

**Issue Jira:** SPK-13  
**Epic:** EP-02 · Camada ETL (Apache Hop)  
**Sprint:** Sprint 2  
**Status:** Em andamento  

---

## 1. Overview

O pipeline de enriquecimento externo completa, para cada produção científica carregada no banco, três campos que o XML do Lattes não fornece de forma confiável: o DOI (quando ausente no XML), o resumo do artigo (`resumo`) e o Fator de Impacto (`jcr`). A CrossRef API fornece DOI e resumo; a OpenAlex API fornece o Impact Factor via ISSN.

Esta spec cobre as subetapas 5.2 (CrossRef) e 5.3 (OpenAlex) do Roadmap ETL — ambas dentro do SPK-13.

---

## 2. Target Users

- **Engenheiro de Dados**: executa o pipeline ETL via Apache Hop e precisa que `doi`, `resumo` e `jcr` sejam preenchidos automaticamente sem intervenção manual.
- **Pesquisador / Visitante** (usuário final): ao buscar uma produção, espera ver o resumo do artigo e os indicadores de qualidade (Qualis e JCR) quando disponíveis.

---

## 3. Problem Statement

Após a carga dos XMLs Lattes e do enriquecimento Qualis (SPK-12), a tabela `producoes` apresenta três campos sistematicamente vazios:

- `doi`: presente em ~88% dos artigos no XML, ausente nos demais.
- `resumo`: o XML do Lattes raramente inclui o abstract do artigo.
- `jcr`: não existe no XML — precisa ser buscado por ISSN em fonte externa.

Sem esses campos, a página de detalhe fica incompleta, o DOI não pode ser exibido como link externo, o `indice_h` dos pesquisadores não pode ser calculado (depende de `jcr`) e a busca semântica não terá texto de qualidade para vetorizar.

---

## 4. User Journeys

### Jornada 1 — Artigo com DOI no XML (CrossRef)

1. O pipeline detecta que `doi` já está preenchido.
2. Consulta CrossRef em `/works/{DOI}` para obter o abstract.
3. Se `abstract` vier preenchido → grava em `producoes.resumo`.
4. Se ausente → `resumo` permanece NULL; a página de detalhe omite a seção.
5. Log registra o resultado.

### Jornada 2 — Artigo sem DOI no XML (CrossRef por título)

1. O pipeline detecta que `doi` está vazio.
2. Busca CrossRef por título normalizado com `query.bibliographic`.
3. Se o score de confiança for > 70: grava o DOI retornado e o abstract (se presente).
4. Se score ≤ 70: ambos permanecem NULL; título registrado como `sem_match_doi` no log.

### Jornada 3 — Enriquecimento de Impact Factor (OpenAlex)

1. Todos os registros com ISSN preenchido são enviados para enriquecimento.
2. ISSNs duplicados são deduplicados antes das chamadas — a API é chamada uma única vez por ISSN.
3. OpenAlex retorna `2yr_mean_citedness` → gravado em `producoes.jcr`.
4. Se HTTP 404 ou campo ausente → `jcr` recebe NULL.
5. Log registra os ISSNs sem correspondência como `sem_match_jcr`.

### Jornada 4 — Falha de API (rate limit ou erro temporário)

1. API retorna erro HTTP (429, 5xx ou timeout).
2. Pipeline tenta novamente até 3 vezes com backoff exponencial (2s, 4s, 8s).
3. Se todas as tentativas falharem: campo recebe NULL e o processamento continua.
4. Erro registrado no log de execução.

---

## 5. Core Features

### F1 — Enriquecimento de DOI por busca via título (CrossRef)
Artigos sem DOI no XML são submetidos a uma busca por título na CrossRef. O DOI é aceito e gravado apenas quando o score de confiança é > 70.

### F2 — Enriquecimento de resumo via CrossRef
Para todo artigo com DOI (vindo do XML ou via F1), o pipeline busca o abstract na CrossRef. Se disponível, grava em `producoes.resumo`. A ausência de abstract é comportamento esperado.

### F3 — Enriquecimento de Impact Factor via OpenAlex
Para todos os registros com ISSN preenchido, o pipeline busca `2yr_mean_citedness` no OpenAlex e grava em `producoes.jcr`. Periódicos não indexados (HTTP 404) recebem NULL.

### F4 — Deduplicação de ISSNs antes das chamadas OpenAlex
O mesmo ISSN pode aparecer em vários artigos do mesmo pesquisador. A API OpenAlex é chamada apenas uma vez por ISSN único, e o resultado é distribuído para todos os artigos com aquele ISSN.

### F5 — Preservação de dados existentes (UPSERT com COALESCE)
Valores já preenchidos de execuções anteriores são preservados se a nova chamada retornar NULL. Nenhum dado é perdido em reprocessamentos.

### F6 — Separação de fluxos (com DOI / sem DOI) e reunificação
O pipeline distingue internamente os dois caminhos CrossRef e os reúne antes da escrita no banco.

### F7 — Registro de não-correspondências no log
- `sem_match_doi`: títulos sem DOI com score suficiente
- `sem_resumo`: DOIs sem abstract na CrossRef
- `sem_match_jcr`: ISSNs que retornaram 404 ou campo nulo no OpenAlex

### F8 — Resiliência a falhas de API
Falhas resultam em NULL para o campo correspondente, nunca em falha do pipeline. Retry com backoff exponencial (3 tentativas: 2s, 4s, 8s).

### F9 — Escopo por tipo de produção
- **CrossRef** (DOI + resumo): apenas `tipo_producao = 'ARTIGO'`
- **OpenAlex** (JCR): todos os registros com ISSN preenchido (artigos)

---

## 6. Success Metrics

| Métrica | Meta |
|---|---|
| Taxa de artigos com `doi` preenchido após enriquecimento | ≥ 90% |
| Taxa de artigos com `resumo` preenchido | ≥ 50% (cobertura parcial é aceitável) |
| Taxa de artigos com `jcr` preenchido | ≥ 70% (OpenAlex cobre ~90% das fontes com ISSN) |
| Pipeline não interrompido por falha de API | 100% dos casos de erro resultam em NULL, não em crash |
| Idempotência confirmada | 2 execuções consecutivas → mesmo resultado |

---

## 7. Constraints

- Apenas APIs gratuitas: CrossRef (sem cadastro) e OpenAlex (cadastro gratuito, 100k req/dia).
- CrossRef exige header `User-Agent` com e-mail para ativar o Polite Pool.
- OpenAlex requer variável de ambiente `OPENALEX_API_KEY`.
- `resumo` e `jcr` aceitam NULL — ausência não é falha.
- DOI via CrossRef por título aceito apenas com score > 70.
- Nenhuma credencial pode ser versionada no Git.
- O pipeline não pode ser interrompido por falha individual de API.

---

## 8. Assumptions

- A tabela `producoes` já existe com os campos `doi`, `resumo` e `jcr` (todos nullable), conforme DDL do SPK-11.
- O UPSERT usa `COALESCE` para preservar valores existentes.
- ~88% dos artigos têm DOI no XML; os restantes são completados via busca por título.
- A cobertura de abstracts na CrossRef é parcial por editora — valores < 100% são esperados.
- O campo `2yr_mean_citedness` do OpenAlex é o equivalente ao JIF da Clarivate (suficiente para o MVP).
- As variáveis `ETL_EMAIL` e `OPENALEX_API_KEY` estão configuradas no ambiente de execução.
- O enriquecimento CrossRef + OpenAlex é executado após a carga das produções (Fase 4) no `spark_etl.hwf`.

---

## 9. Out of Scope

- Enriquecimento de estrato Qualis → **SPK-12 (concluído)**
- Spike de modelos de embedding → **SPK-14**
- Geração de vetores / embeddings → Sprint futura
- Enriquecimento de EVENTO, LIVRO, CAPITULO com resumo (sem ISSN padronizado)
- Armazenamento de metadados extras da CrossRef além de DOI e abstract
- Cálculo de `indice_h` — calculado na Fase 5 (após JCR estar preenchido)

---

## Prompt de Implementação

Leia esta spec e implemente o SPK-13 seguindo o **Roadmap ETL (seções 5.2 e 5.3)** como guia técnico principal. Baseie-se também em `SDD/constitution.md`, `SDD/plan.md` e `SDD/memory.md`.

**O que implementar:**

1. **`etl/pipelines/crossref_enriquecimento.hpl`** (seção 5.2 do roadmap):
   - `TableInput`: SELECT id, titulo, doi FROM producoes WHERE tipo_producao = 'ARTIGO'
   - `FilterRows`: separa artigos com DOI dos sem DOI
   - **Ramo com DOI**: `HTTP Client` → `GET /works/${doi}?select=DOI,title,abstract` → extrai abstract
   - **Ramo sem DOI**: `HTTP Client` → `GET /works?query.bibliographic=${titulo}&rows=1&select=DOI,title,abstract,score` → filtra score > 70 → extrai DOI + abstract
   - `Modified JavaScript Value`: extrai campos do JSON de resposta
   - `Append Streams`: reúne os dois ramos
   - `ExecSQL`: `UPDATE producoes SET doi = COALESCE(?,doi), resumo = COALESCE(?,resumo) WHERE id = ?`
   - `WriteToLog`: artigos sem match (sem_match_doi) e sem abstract (sem_resumo)
   - Header obrigatório: `User-Agent: SPARK-ETL/1.0 (mailto:${ETL_EMAIL})`
   - Retry: 3 tentativas com backoff 2s/4s/8s

2. **`etl/pipelines/openalex_enriquecimento.hpl`** (seção 5.3 do roadmap):
   - `TableInput`: SELECT DISTINCT issn, id FROM producoes WHERE issn IS NOT NULL AND issn != ''
   - `SortRows` + `Unique` por ISSN (deduplicação antes das chamadas)
   - `HTTP Client`: `GET https://api.openalex.org/sources/issn:${issn}?select=issn_l,display_name,2yr_mean_citedness&api_key=${OPENALEX_API_KEY}`
   - `Modified JavaScript Value`: extrai `2yr_mean_citedness`
   - Join de volta ao fluxo principal pelo ISSN
   - `ExecSQL`: `UPDATE producoes SET jcr = COALESCE(?,jcr) WHERE issn = ?`
   - HTTP 404 ou campo null → NULL em jcr
   - `WriteToLog`: ISSNs sem match (sem_match_jcr)

3. **Integrar ambos no `etl/workflows/spark_etl.hwf`** após o step de Qualis, em sequência: Qualis → CrossRef → OpenAlex → Registrar sem match → Registrar sucesso

4. **Atualizar parâmetros** nos scripts `run-etl.ps1` e `run-etl.sh` com `ETL_EMAIL` e `OPENALEX_API_KEY`

5. **Atualizar `etl_logs.detalhes`** ao final com `sem_match_doi`, `sem_resumo` e `sem_match_jcr`

**Restrições obrigatórias:**
- Todo UPSERT usa `COALESCE` — nunca sobrescreve valor existente com NULL
- Falha de API resulta em NULL, não em erro do pipeline
- Apenas ARTIGO para CrossRef; ISSN não nulo para OpenAlex
- Commit no formato `feat(SPK-13): descrição`

Ao concluir, renomeie este arquivo para `spk13_spec_CONCLUIDA.md` e atualize o `SDD/memory.md`.
