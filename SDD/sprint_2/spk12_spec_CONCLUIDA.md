# SPK-12 — US-06: Integração com base Qualis CAPES

**Sprint:** II  
**Status:** Em andamento  
**Assignee:** Glenda Santana  
**Jira:** SPK-12

---

## 1. Overview

As produções científicas carregadas pelo pipeline ETL possuem o campo `qualis` vazio. O Qualis CAPES é o sistema oficial de classificação de periódicos científicos brasileiros, e seu estrato (A1, A2, ..., C) é um dos indicadores bibliométricos mais relevantes para avaliação de pesquisadores. Esta spec cobre o enriquecimento das produções existentes no banco com o estrato Qualis correspondente, a partir da planilha oficial da Plataforma Sucupira.

---

## 2. Target Users

**Coordenadores e gestores da UNEB** que consultam os painéis analíticos do SPARK para avaliar a produção científica do departamento por estrato Qualis.

**Pesquisadores** que desejam visualizar o estrato de seus artigos publicados em periódicos indexados na base CAPES.

**Administradores do sistema** responsáveis por manter a base de dados atualizada a cada novo ciclo de classificação Qualis.

---

## 3. Problem Statement

Atualmente, todas as produções científicas do tipo ARTIGO têm o campo `qualis` nulo no banco de dados. Sem essa informação, os painéis analíticos não conseguem estratificar a produção por qualidade do periódico, e as métricas bibliométricas do departamento ficam incompletas. O Qualis é a principal referência de qualidade utilizada pela CAPES na avaliação de programas de pós-graduação, tornando sua ausência um bloqueio para os relatórios gerenciais do SPARK.

---

## 4. User Journeys

### Jornada 1 — Administrador executa o enriquecimento Qualis

1. O administrador obtém a planilha Qualis da Plataforma Sucupira (exportação manual do quadriênio 2017–2020)
2. O administrador disponibiliza o arquivo no diretório configurado para o pipeline
3. O administrador aciona o pipeline de enriquecimento
4. O sistema cruza cada produção do tipo ARTIGO com a planilha pelo ISSN do periódico
5. Quando o ISSN localiza o periódico, o sistema registra o maior estrato encontrado entre as áreas de avaliação
6. Quando o ISSN não localiza, o sistema tenta o cruzamento pelo nome do periódico
7. Ao final, o sistema gera um log indicando quantas produções receberam Qualis e quantas ficaram sem correspondência
8. O administrador consulta o log para avaliar a taxa de cobertura

### Jornada 2 — Coordenador consulta produção por estrato

1. O coordenador acessa o painel analítico do SPARK
2. Filtra por departamento e período
3. O sistema exibe a distribuição de artigos por estrato Qualis (A1, A2, B1, etc.)
4. O coordenador identifica a concentração de produção nos estratos superiores

### Jornada 3 — Reprocessamento após nova planilha Qualis

1. A CAPES publica uma nova classificação de periódicos
2. O administrador substitui o arquivo da planilha pelo novo
3. O pipeline é reexecutado sobre as produções já existentes
4. O campo `qualis` das produções é atualizado sem criar duplicatas
5. Produções que já tinham Qualis preenchido só têm o valor substituído se o novo for diferente

---

## 5. Core Features

### 5.1 — Enriquecimento de `qualis` por ISSN

O sistema deve cruzar cada produção do tipo ARTIGO que possua ISSN com a planilha Qualis CAPES, associando o estrato correspondente ao periódico. Um mesmo periódico pode aparecer em múltiplas áreas de avaliação com estratos diferentes — o sistema deve registrar apenas o **estrato mais alto** encontrado.

### 5.2 — Fallback por nome do periódico

Quando o ISSN de uma produção não localiza correspondência na planilha, o sistema deve tentar o cruzamento pelo nome do periódico (campo `nome_veiculo`), de forma que variações de ISSN não resultem em perda desnecessária de cobertura.

### 5.3 — Log de produções sem correspondência

Ao final de cada execução, o sistema deve registrar na entrada de log (`etl_logs`) a lista de periódicos que não encontraram correspondência nem por ISSN nem por nome, permitindo que o administrador identifique lacunas de cobertura.

### 5.4 — UPSERT idempotente

O enriquecimento deve poder ser reexecutado sobre a base existente sem criar duplicatas. Se uma produção já possui `qualis` preenchido e o novo processamento também encontra um valor, o campo deve ser atualizado. Se o novo processamento não encontra correspondência (retorna nulo), o valor anterior deve ser **preservado**.

### 5.5 — Cobertura mínima de 70%

O pipeline deve atingir taxa de correspondência superior a 70% nas produções do tipo ARTIGO presentes nos currículos de teste, medida ao final da execução e registrada no log.

---

## 6. Success Metrics

| Métrica | Critério de aceitação |
|---------|----------------------|
| Taxa de match (ISSN + fallback nome) | Superior a 70% dos artigos nos currículos de teste |
| Campo `qualis` populado | Todas as produções com ISSN correspondente na planilha têm `qualis` preenchido |
| Idempotência | Duas execuções consecutivas produzem o mesmo resultado sem duplicatas |
| Log de sem-match | `etl_logs.detalhes` contém a lista `sem_match_qualis` com os ISSNs não encontrados |
| Execução sem interrupção | Produções sem correspondência não interrompem o processamento das demais |

---

## 7. Constraints

- A planilha Qualis **não possui API** — o arquivo precisa ser obtido manualmente da Plataforma Sucupira e disponibilizado localmente antes da execução do pipeline
- O pipeline deve processar somente produções do tipo **ARTIGO** com ISSN preenchido; tipos EVENTO, LIVRO e CAPITULO não possuem ISSN na maioria dos currículos e ficam com `qualis = NULL`
- Um mesmo periódico pode ter estratos diferentes por área de avaliação — o pipeline deve registrar apenas o estrato mais alto, sem armazenar a área de avaliação no banco (fora do escopo do MVP)
- O pipeline deve ser implementado em **Apache Hop**, conforme a constitution do projeto
- Toda escrita na tabela `producoes` deve usar UPSERT com `ON CONFLICT DO UPDATE`, conforme a constitution

---

## 8. Assumptions

- A planilha Qualis do quadriênio 2017–2020 é a classificação de referência para este sprint
- O ISSN nas produções já está normalizado para o formato com hífen (`XXXX-XXXX`) pelo pipeline SPK-11
- A tabela `producoes` e o campo `qualis` já existem no banco (criados na Sprint I / SPK-36)
- O pipeline SPK-11 já foi executado e a tabela `producoes` está populada com os dados dos 8 currículos de teste (247 artigos)
- Periódicos sem correspondência na planilha terão `qualis = NULL` — isso é comportamento esperado e não configura falha do sistema

---

## 9. Out of Scope

- Integração com a API da Plataforma Sucupira (não existe — download manual é o único meio)
- Armazenamento da área de avaliação Qualis por periódico
- Enriquecimento de produções dos tipos EVENTO, LIVRO e CAPITULO com Qualis
- Lookup de DOI e resumo via CrossRef (SPK-13)
- Lookup de Impact Factor via OpenAlex (SPK-14)
- Atualização automática da planilha Qualis a cada nova publicação da CAPES
- Interface gráfica para upload da planilha pelo administrador

---

## Prompt para implementação autônoma

```
Leia os seguintes arquivos antes de qualquer ação:
- SDD/constitution.md
- SDD/plan.md
- SDD/memory.md
- SDD/sprint_2/spk12_spec.md
- RoadMap_para_ETL.pdf (seções 2.2, 4.1, 5.1, 6.4, 10 e 11.3)

Implemente o SPK-12: enriquecimento das produções com Qualis CAPES.

Contexto do que já existe:
- Banco PostgreSQL rodando em Docker (container spark-db-1, porta 5432, banco spark, user spark)
- Tabela producoes populada com 462 produções (247 artigos) — campo qualis está NULL em todos
- Campo qualis já existe na tabela: character varying(5), nullable
- Pipeline ETL rodando em Apache Hop 2.15.0 (C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop)
- Projeto Hop registrado como spark apontando para etl/
- ISSN já vem normalizado com hífen (XXXX-XXXX) nas produções

O que deve ser implementado:
1. Pipeline Apache Hop: etl/pipelines/qualis_enriquecimento.hpl
   - Carregar a planilha qualis_capes.csv via parâmetro QUALIS_CSV
   - Normalizar ISSN da planilha para o formato com hífen
   - Criar coluna numérica auxiliar para o estrato (A1=10, A2=9, A3=8, A4=7, B1=6,
     B2=5, B3=4, B4=3, B5=2, C=1) para permitir MAX correto — string pura dá resultado
     errado (em ordem alfabética A2 > A1, mas A1 é melhor)
   - Stream Lookup: producoes.issn = qualis.ISSN → obter estrato máximo por ISSN
   - Fallback por nome do periódico quando ISSN não encontrar resultado
   - UPSERT em producoes: UPDATE qualis = COALESCE(novo, existente)
   - Coletar ISSNs sem match e registrar em etl_logs.detalhes como sem_match_qualis

2. Adicionar a execução do novo pipeline no workflow etl/workflows/spark_etl.hwf
   após Pipeline Producoes e antes de Registrar sucesso

3. Atualizar etl/scripts/run-etl.ps1 e run-etl.sh para aceitar parâmetro QUALIS_CSV

4. Atualizar etl/README.md com instruções de como obter a planilha Qualis no Sucupira
   e como passar o caminho do arquivo para o pipeline

Regras obrigatórias (da constitution):
- Todo UPSERT usa ON CONFLICT DO UPDATE com COALESCE para não sobrescrever valores já enriquecidos
- Nenhum secret no repositório
- Pipeline implementado em Apache Hop — não usar Python ou shell para a lógica de enriquecimento
- Ao finalizar, renomear spk12_spec.md para spk12_spec_CONCLUIDA.md
- Atualizar SDD/memory.md com o que foi implementado

Critério de sucesso: taxa de match > 70% nos 247 artigos de teste; campo qualis populado;
etl_logs.detalhes contém sem_match_qualis; duas execuções consecutivas produzem o mesmo resultado.

Caso tenha dúvidas sobre a implementação, pergunte antes de tomar qualquer decisão.
```
