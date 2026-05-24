# SPK-89 — Fase 5: Atualização de Métricas Bibliométricas

**Issue Jira:** SPK-89
**Epic:** EP-02 · Camada ETL (Apache Hop)
**Sprint:** Sprint 2
**Status:** Em andamento

---

## 1. Overview

Após a carga e o enriquecimento das produções científicas, o pipeline calcula e persiste três métricas bibliométricas por pesquisador — total de produções, total de publicações A1/A2 e índice H — diretamente no banco de dados. Os valores são calculados apenas para os pesquisadores processados na execução corrente e gravados em campos pré-calculados, eliminando qualquer cálculo em tempo de consulta pela API.

---

## 2. Target Users

- **Engenheiro de Dados**: executa o pipeline ETL e precisa que as métricas sejam atualizadas automaticamente ao final de cada carga, sem intervenção manual.
- **Administrador / Gestor acadêmico**: visualiza no painel os indicadores de desempenho dos pesquisadores (total de produções, publicações de alto impacto, índice H) e precisa que reflitam o estado atual do banco.
- **Pesquisador / Visitante** (usuário final): acessa o perfil de um pesquisador e espera ver métricas corretas e atualizadas.

---

## 3. Problem Statement

Após a execução das Fases 1 a 4 do pipeline (extração, transformação, enriquecimento e carga), a tabela `pesquisadores` permanece com os campos `total_producoes`, `total_a1_a2` e `indice_h` zerados. Esses campos existem justamente para evitar cálculos custosos em tempo de consulta, mas sem um passo dedicado ao final do ETL, nunca são preenchidos.

Como consequência:

- Perfis de pesquisadores exibem sempre zero em todos os indicadores.
- A API não consegue ordenar ou filtrar pesquisadores por desempenho bibliométrico.
- O índice H — que depende do campo `jcr` preenchido pelo enriquecimento OpenAlex (SPK-13) — não pode ser calculado enquanto esse passo estiver ausente.

---

## 4. User Journeys

### Jornada 1 — ETL processa currículos e métricas são atualizadas

1. O Engenheiro de Dados executa o pipeline ETL com os XMLs Lattes dos pesquisadores.
2. As Fases 1 a 4 concluem (extração, transformação, enriquecimento, carga).
3. O pipeline identifica os pesquisadores que foram processados na execução corrente.
4. Para cada um deles, calcula `total_producoes`, `total_a1_a2` e `indice_h` com base nas produções já carregadas e enriquecidas.
5. Os três campos são atualizados no banco.
6. A execução registra sucesso no log.

### Jornada 2 — Reprocessamento de currículo já existente

1. Um pesquisador tem novas produções adicionadas ao XML e o ETL é reexecutado.
2. As métricas são recalculadas do zero a partir das produções atuais no banco.
3. Os campos `total_producoes`, `total_a1_a2` e `indice_h` são sobrescritos com os novos valores corretos.
4. Nenhuma execução anterior gera valores inconsistentes.

### Jornada 3 — Pesquisador sem produções

1. O pipeline processa um pesquisador cujo XML não contém produções bibliográficas.
2. Os campos `total_producoes` e `total_a1_a2` recebem zero.
3. `indice_h` recebe zero (sem produções com JCR preenchido).
4. O pipeline não falha por ausência de produções.

### Jornada 4 — Pesquisador sem JCR nas produções

1. O pipeline processa um pesquisador cujas produções não têm `jcr` preenchido (ex.: apenas eventos e capítulos).
2. `total_producoes` e `total_a1_a2` são calculados normalmente.
3. `indice_h` recebe zero (produções sem JCR são excluídas do cálculo).
4. O pipeline não falha.

---

## 5. Core Features

### F1 — Cálculo de total de produções

Ao final de cada execução do ETL, o sistema conta todas as produções associadas ao pesquisador, independente de tipo (`ARTIGO`, `EVENTO`, `LIVRO`, `CAPITULO`), Qualis ou JCR, e grava o resultado em `pesquisadores.total_producoes`.

### F2 — Cálculo de publicações A1 e A2

O sistema conta apenas as produções com `qualis IN ('A1', 'A2')` e grava em `pesquisadores.total_a1_a2`. Produções de outros estratos ou sem Qualis não são contabilizadas neste campo.

### F3 — Cálculo do índice H

O sistema calcula o índice H do pesquisador: o maior número N tal que N produções possuem `jcr >= N`. Apenas produções com `jcr` preenchido participam deste cálculo. O resultado é gravado em `pesquisadores.indice_h`.

### F4 — Atualização restrita aos pesquisadores da execução corrente

O cálculo e a atualização ocorrem apenas para os pesquisadores processados na execução atual do pipeline. Pesquisadores já no banco, mas não incluídos na carga corrente, não são tocados.

### F5 — Idempotência

Executar o pipeline duas vezes consecutivas com os mesmos XMLs produz o mesmo resultado nos três campos. Não há acúmulo de contagens nem divergência entre execuções.

---

## 6. Success Metrics

| Métrica                                                                         | Meta                                          |
| -------------------------------------------------------------------------------- | --------------------------------------------- |
| `total_producoes`, `total_a1_a2` e `indice_h` preenchidos após execução | 100% dos pesquisadores processados            |
| Pesquisadores fora da execução corrente inalterados                            | 100%                                          |
| Idempotência confirmada                                                         | 2 execuções consecutivas → mesmo resultado |
| Pipeline não interrompido por pesquisador sem produções ou sem JCR            | 100% dos casos                                |
| `indice_h = 0` para pesquisadores sem produções com JCR preenchido           | Comportamento correto verificado              |

---

## 7. Constraints

- As métricas devem ser pré-calculadas e gravadas no banco — nenhum cálculo em tempo de consulta é permitido pela API.
- Apenas os pesquisadores da execução atual são atualizados (não a tabela inteira).
- O cálculo do `indice_h` exclui produções com `jcr = NULL`.
- O passo de métricas é executado após a Fase 4 (carga de produções) e após o enriquecimento completo (Qualis, CrossRef e OpenAlex) — `jcr` e `qualis` já devem estar preenchidos.
- O pipeline não pode ser interrompido por falha no cálculo de métricas de um pesquisador individual.

---

## 8. Assumptions

- A tabela `pesquisadores` já possui os campos `total_producoes`, `total_a1_a2` e `indice_h` com valor padrão 0, conforme DDL do SPK-11.
- O enriquecimento Qualis (SPK-12) e CrossRef/OpenAlex (SPK-13) já foram executados nesta mesma carga — `qualis` e `jcr` estão com os melhores valores disponíveis antes deste passo.
- Os 8 pesquisadores de teste têm produções suficientes para validar os três campos.
- `indice_h = 0` é um valor válido — não indica erro, apenas ausência de produções com `jcr >= 1`.
- O pipeline já dispõe dos `pesquisador_id` processados na execução corrente, obtidos do fluxo de pesquisadores carregados.
- Paulo Jorge Silveira Ferreira (sem produções no XML) deve resultar em zeros nos três campos — não é um caso de erro.

---

## 9. Out of Scope

- Cálculo em tempo de consulta na API — os campos são sempre pré-calculados.
- Exibição das métricas no frontend → Sprint futura.
- Endpoints da API para leitura de métricas → Sprint futura.
- Métricas além de `total_producoes`, `total_a1_a2` e `indice_h` (ex.: fator H5, coautoria) → fora do MVP.
- Acionamento do Worker de Embeddings → **Fase 6 (Sprint futura)**.
- Reprocessamento em batch de todos os pesquisadores do banco → fora do escopo desta story.

---

## Prompt de Implementação

Leia esta spec e implemente o SPK-89 seguindo o **RoadMap_para_ETL.pdf (Seção 8 — Fase 5)** como guia técnico principal. Baseie-se também em `SDD/constitution.md`, `SDD/plan.md` e `SDD/memory.md`.

**O que implementar:**

1. **Adicionar step `Execute SQL` ao `etl/workflows/spark_etl.hwf`** — posicionado após o step de enriquecimento OpenAlex e antes de "Registrar sucesso":

   - Executa uma vez por pesquisador processado na execução corrente
   - SQL exato (conforme Seção 8 do roadmap):

   ```sql
   UPDATE pesquisadores SET
     total_producoes = (
       SELECT COUNT(*) FROM producoes WHERE pesquisador_id = ?
     ),
     total_a1_a2 = (
       SELECT COUNT(*) FROM producoes
       WHERE pesquisador_id = ? AND qualis IN ('A1', 'A2')
     ),
     indice_h = (
       SELECT COUNT(*) FROM (
         SELECT jcr, ROW_NUMBER() OVER (ORDER BY jcr DESC) AS pos
         FROM producoes
         WHERE pesquisador_id = ? AND jcr IS NOT NULL
       ) ranked
       WHERE jcr >= pos
     )
   WHERE id = ?;
   ```
2. **Alimentar o step com os `pesquisador_id` da execução corrente** — obtidos do fluxo de pesquisadores já processados no workflow (não fazer SELECT * na tabela inteira).
3. **Validar após execução** com os 8 currículos de teste:

   - `total_producoes` deve bater com as contagens já conhecidas no `memory.md` (ARTIGO: 247, EVENTO: 161, CAPITULO: 40, LIVRO: 14 — distribuídos entre os 7 pesquisadores com produções)
   - `total_a1_a2` deve bater com os estratos A1/A2 preenchidos pelo SPK-12 (A1: 64, A2: 40)
   - `indice_h` calculado a partir do `jcr` preenchido pelo SPK-13
   - Paulo Jorge Silveira Ferreira deve ter `total_producoes = 0`, `total_a1_a2 = 0`, `indice_h = 0`
4. **Confirmar idempotência**: executar o pipeline duas vezes e verificar que os três campos não mudam na segunda execução.

**Restrições obrigatórias:**

- Nunca atualizar pesquisadores fora da execução corrente.
- Falha no cálculo de um pesquisador não interrompe o pipeline — registrar no log e continuar.
- Commit no formato `feat(SPK-89): descrição`.

Ao concluir, renomeie este arquivo para `spk89_spec_CONCLUIDA.md` e atualize o `SDD/memory.md`.

---
