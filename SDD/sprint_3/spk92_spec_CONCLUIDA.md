# SPK-92 · API FastAPI: busca textual, semântica e endpoints de suporte

**Sprint:** 3 | **Épico:** EP-03 · Back-End Python, API REST e Deploy
**Jira:** SPK-92 | **Story Points:** 8

---

## 1. Overview

O SPARK precisa de uma API REST que o front-end Next.js possa consumir para entregar as quatro telas do protótipo: busca com dois modos (textual e semântica), listagem de resultados com filtros, detalhe de produção e perfil do pesquisador. Esta história cobre todos os endpoints públicos necessários para essas telas, mais dois endpoints auxiliares que alimentam os cards de estatísticas da home e o filtro dinâmico de tipos. A API roda localmente conectada ao banco Docker do Sprint 2.

---

## 2. Target Users

| Persona                                 | Contexto de uso                                                                                |
| --------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **Pesquisador UNEB**              | Busca produções científicas da instituição para benchmarking e referência bibliográfica |
| **Estudante de pós-graduação** | Explora a produção dos orientadores antes de selecionar uma linha de pesquisa                |
| **Gestor acadêmico**             | Analisa indicadores bibliométricos (Qualis, JCR, índice-h) de pesquisadores específicos     |
| **Front-end Next.js**             | Consome todos os endpoints desta história para renderizar as telas do protótipo              |

---

## 3. Problem Statement

Atualmente o banco de dados do SPARK está populado com 462 produções enriquecidas (Qualis, DOI, resumo, JCR) e os pesquisadores têm métricas bibliométricas calculadas — mas não há forma de consultar esses dados fora de um cliente SQL. O front-end não tem superfície de acesso, o que impede qualquer validação das telas do protótipo ou demonstração para stakeholders. Esta história cria a camada de acesso que transforma o banco num produto utilizável.

---

## 4. User Journeys

### UC-01 · Busca textual por palavras-chave

1. Usuário abre a home e vê o card de estatísticas com total de produções, pesquisadores e embeddings gerados.
2. Digita um termo (ex: "aprendizado de máquina") e seleciona o modo **textual**.
3. O sistema retorna até 20 produções por página, ordenadas por relevância, com título, veículo, ano, Qualis, JCR e nome do pesquisador.
4. Usuário refina usando operadores AND / OR / NOT.
5. Usuário navega para a próxima página sem recarregar a lista inteira.

### UC-02 · Busca semântica com filtros

1. Usuário digita uma frase em linguagem natural (ex: "epidemiologia de arboviroses no nordeste") e seleciona o modo **semântica**.
2. O sistema retorna até 10 produções com pontuação de similaridade visível em cada card.
3. Usuário aplica filtros — intervalo de ano, Qualis mínimo, faixa de JCR, tipo de produção — sem recarregar a página.
4. Chips de filtros ativos aparecem na barra acima dos resultados; cada chip pode ser removido individualmente.

### UC-03 · Detalhe de produção

1. Usuário clica em um card de resultado.
2. Sistema exibe todos os campos disponíveis da produção: título, veículo, ISSN, DOI (como link externo), resumo, Qualis, JCR, tipo, ano.
3. Abaixo dos dados da produção aparece um bloco com o pesquisador responsável: nome, departamento, campus, total de produções, índice-h, total A1+A2.
4. Campos não disponíveis (NULL) são simplesmente omitidos — não aparecem como vazio ou "N/A".

### UC-04 · Perfil do pesquisador

1. Usuário clica no nome de um pesquisador no card de resultado ou acessa diretamente pelo URL.
2. Sistema exibe: nome, departamento, campus, resumo do currículo, data de atualização e métricas bibliométricas (total de produções, índice-h, total A1+A2).
3. Aba **produções**: lista paginada (20 por página) com título, veículo, ano, Qualis e JCR de cada produção.
4. Aba **indicadores**: dois gráficos — produções por ano e distribuição por estrato Qualis — alimentados por um endpoint dedicado de estatísticas.

---

## 5. Core Features

### 5.1 Busca textual

- Usuários podem buscar produções por palavras-chave com suporte a operadores booleanos (AND, OR, NOT).
- Resultados paginados em até 20 itens por página, ordenados por relevância textual.
- Filtros aplicáveis: intervalo de ano de publicação, estrato Qualis (lista ou atalho "B1+" que expande para B1–C), faixa de JCR (mínimo e máximo), incluir produções sem JCR, tipos de produção, pesquisador específico.
- Quando não há resultados para os critérios fornecidos, o sistema retorna lista vazia sem erro.

### 5.2 Busca semântica

- Usuários podem buscar por intenção em linguagem natural.
- Sistema retorna os 10 resultados mais próximos semanticamente, cada um com pontuação de similaridade entre 0 e 1.
- Aceita os mesmos filtros da busca textual.
- A pontuação de similaridade é visível para o usuário em cada card de resultado.

### 5.3 Card de estatísticas da home

- A home exibe total de produções, total de pesquisadores, total de vetores gerados e data da última carga ETL.
- Esses números vêm de um endpoint dedicado e refletem o estado atual do banco.

### 5.4 Filtro dinâmico de tipos

- O painel de filtros da tela de resultados lista apenas os tipos de produção que existem no banco (ex: ARTIGO, EVENTO, CAPITULO, LIVRO), com a contagem de cada um.
- A lista é dinâmica — não é hardcoded no front-end.

### 5.5 Detalhe de produção

- Usuários podem acessar todos os metadados de uma produção específica, incluindo dados do pesquisador associado aninhados na resposta.
- DOI é entregue como valor puro; o front-end o renderiza como link externo.

### 5.6 Perfil do pesquisador

- Usuários podem consultar o perfil completo de um pesquisador com métricas pré-calculadas.
- Produções do pesquisador são listadas de forma paginada (20 por página).
- Dados para gráficos de evolução anual e distribuição Qualis são entregues por um endpoint dedicado de estatísticas.

---

## 6. Success Metrics

| Métrica                                | Critério de aceite                                                                                                                                                                              |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Busca textual responde dentro do SLA    | Tempo de resposta < 30 s em ambiente local com banco Docker                                                                                                                                      |
| Busca semântica responde dentro do SLA | Tempo de resposta < 5 s em ambiente local com banco Docker                                                                                                                                       |
| Todos os endpoints documentados         | Swagger em `/docs` funcional com todos os endpoints desta história                                                                                                                            |
| Cobertura de testes                     | Testes unitários passando para: busca textual (3 cenários), busca semântica (3 cenários), geração de embeddings, ranqueamento por similaridade, endpoint `/api/pesquisadores/{id}/stats` |
| Filtros sem reload                      | Aplicação de filtros na tela de resultados não recarrega a página inteira                                                                                                                    |
| Campos NULL omitidos                    | Nenhum campo NULL retornado como string vazia ou "N/A" nas respostas                                                                                                                             |
| Resultado vazio retorna 200             | Nenhum endpoint retorna 404 para ausência de dados                                                                                                                                              |

---

## 7. Constraints

- A API deve funcionar localmente conectada ao banco Docker configurado no Sprint 2 (`DATABASE_URL` via `.env`).
- Paginação máxima de 20 itens por página em todos os endpoints de listagem — não negociável.
- Embeddings gerados exclusivamente pelo modelo local `all-MiniLM-L6-v2` — nenhuma API externa pode ser chamada para isso.
- O campo `similarity_score` é obrigatório em toda resposta de busca semântica; sua ausência é uma quebra de contrato.
- Acesso de leitura é público — nenhum endpoint desta história requer autenticação.
- Métricas bibliométricas (`total_producoes`, `indice_h`, `total_a1_a2`) devem ser lidas dos campos pré-calculados na tabela `pesquisadores` — nunca recalculadas em tempo de consulta.

---

## 8. Assumptions

- O banco Docker do Sprint 2 está rodando com os dados das 8 XMLs Lattes e enriquecimento Qualis/CrossRef/OpenAlex/métricas já aplicados (Sprints 1 e 2 concluídos).
- O worker de embeddings que popula a tabela `vetores` será implementado separadamente (SPK-100); nesta história assume-se que `vetores` pode estar vazia durante o desenvolvimento dos testes unitários, mas o endpoint semântico deve funcionar quando registros existirem.
- O filtro de Qualis com atalho "B1+" (expandindo para B1, B2, B3, B4, B5, C) é expandido pelo back-end, não pelo front-end.
- O filtro `jcr_nulo: true` permite que o usuário inclua produções sem JCR (eventos, livros, capítulos) nos resultados — traduz para `jcr IS NULL` no banco.
- Os tipos de produção existentes no banco são: ARTIGO, EVENTO, CAPITULO, LIVRO — mas o endpoint os descobre dinamicamente.

---

## 9. Out of Scope

- Autenticação e endpoints do painel Admin (cobertos em história separada).
- Endpoint `POST /internal/trigger-etl` (coberto em história separada).
- Worker de geração de embeddings (coberto em SPK-100).
- Deploy em Railway — esta história é exclusivamente local.
- Busca por pesquisador pelo nome (a busca textual aceita `pesquisador_id`, não texto livre de nome).
- Exportação de resultados em CSV ou PDF.
- Notificações push ou qualquer funcionalidade em tempo real.

---

## Subtarefas

| Jira    | Descrição                                                                                                      |
| ------- | ---------------------------------------------------------------------------------------------------------------- |
| SPK-98  | Criar estrutura do projeto FastAPI com asyncpg, routers (search, producoes, pesquisadores) e schemas Pydantic    |
| SPK-99  | Implementar `POST /api/search/text` com FTS via tsvector e paginação de 20 itens                             |
| SPK-100 | Implementar `POST /api/search/semantic` com embeddings all-MiniLM-L6-v2 e similaridade de cosseno via pgvector |
| SPK-101 | Escrever testes unitários para busca textual, semântica e geração de embeddings                              |
| SPK-112 | Implementar `GET /api/stats` e `GET /api/producoes/tipos`                                                    |
| SPK-113 | Implementar `GET /api/producoes/{id}` com pesquisador aninhado                                                 |
| SPK-114 | Implementar `GET /api/pesquisadores/{id}`, `/{id}/producoes` e `/{id}/stats`                               |

Pra cada subtarefa, verifique se há detalhes no cartão do jira pra ela. Algumas tem e são muito importantes

---

## Definição de Pronto (DoD)

- Código no Git com commits referenciando `SPK-92` (ou subtarefa correspondente).
- Todos os endpoints funcionais e documentados no Swagger em `/docs`.
- Testes unitários passando para os cenários obrigatórios.
- SLAs de performance validados localmente (textual < 30 s, semântica < 5 s).
- Demonstrado e aprovado na Sprint Review.

---

## Prompt de implementação

Leia esta spec do início ao fim antes de qualquer ação. Em seguida:

1. Leia `SDD/constitution.md` e `SDD/plan.md` para confirmar restrições arquiteturais.
2. Leia `SDD/memory.md` para entender o estado atual do banco e dos dados disponíveis.
3. Implemente a estrutura do projeto FastAPI conforme `SDD/plan.md` (seção *Project Structure*), criando os arquivos: `backend/app/main.py`, `backend/app/database.py`, `backend/app/schemas.py`, `backend/app/routers/search.py`, `backend/app/routers/producoes.py`, `backend/app/routers/pesquisadores.py`, `backend/app/services/text_search.py`, `backend/app/services/semantic_search.py`, `backend/app/services/embeddings.py`.
4. Implemente cada endpoint na ordem das subtarefas (SPK-98 → SPK-99 → SPK-112 → SPK-113 → SPK-114 → SPK-100 → SPK-101).
5. Para cada endpoint, valide: retorno 200 com lista vazia quando não há dados; campos NULL omitidos; paginação máxima de 20.
6. Escreva os testes unitários em `backend/tests/unit/` cobrindo os cenários obrigatórios desta spec.
7. Ao finalizar, atualize `SDD/memory.md` com o que foi implementado e renomeie este arquivo para `spk92_spec_CONCLUIDA.md`.
