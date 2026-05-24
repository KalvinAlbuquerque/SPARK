# SPK-93 · Worker de Embeddings e Endpoints Internos

**Issue:** SPK-93 — US-11  
**Epic:** EP-03 · Back-End Python, API REST e Deploy  
**Sprint:** Sprint 3  
**Subtarefas:** SPK-102, SPK-103, SPK-104

---

## 1. Overview

O SPARK precisa que suas produções científicas possam ser encontradas por busca semântica e que o administrador do sistema possa manter a base de dados atualizada sem depender de acesso direto ao servidor. Este spec cobre três peças que fecham esse ciclo: o worker que gera vetores para busca semântica, os endpoints internos que permitem ao pipeline ETL e ao painel admin acionar o processamento via HTTP, e as operações de gerenciamento de pesquisadores (importar XMLs em lote, cadastrar novo pesquisador, re-sincronizar individualmente) que o painel admin expõe ao administrador.

---

## 2. Target Users

**Administrador do sistema (Admin SPARK)**  
Responsável por manter a base de pesquisadores e produções atualizada. Acessa o sistema via painel administrativo autenticado. Precisa importar novos XMLs Lattes, cadastrar pesquisadores, re-sincronizar currículos individualmente quando necessário, e acionar a geração de vetores para manter a busca semântica funcional — tudo sem precisar de acesso direto ao servidor.

**Pipeline ETL automatizado (Apache Hop)**  
Componente não humano que, após concluir o carregamento e enriquecimento das produções, aciona automaticamente via HTTP o processamento de vetores para garantir que os dados recém-importados fiquem disponíveis para busca semântica sem intervenção manual.

---

## 3. Problem Statement

O sistema possui uma API de busca semântica funcional, mas os resultados estão sempre vazios porque nenhuma produção tem vetor gerado. A busca semântica é inutilizável.

Além disso, manter a base atualizada exige que o administrador tenha o Apache Hop instalado localmente e acesso direto ao servidor — uma barreira operacional que impede que o sistema seja gerenciado de forma autônoma. O protótipo do painel admin já prevê um fluxo de interface para essas operações, mas os endpoints de back-end que sustentam esse fluxo ainda não existem.

O terceiro problema é consequência dos dois: sem os endpoints de acionamento via HTTP, o pipeline ETL não consegue notificar o sistema para gerar vetores ao final de cada carga, criando uma dependência manual que quebra o ciclo de atualização automática.

---

## 4. User Journeys

### Jornada 1 — Admin importa XMLs Lattes em lote

1. Admin acessa o painel administrativo com suas credenciais.
2. No painel, na seção de pesquisadores, Admin clica em **"importar XML"**.
3. Admin seleciona um ou mais arquivos XML de currículos Lattes.
4. O sistema processa os arquivos em sequência: extrai pesquisadores e produções, enriquece com Qualis, CrossRef e OpenAlex, calcula métricas bibliométricas e gera vetores para busca semântica.
5. Admin recebe um resumo com os totais processados por fase (pesquisadores, produções, correspondências de enriquecimento, vetores gerados, eventuais erros).
6. Os dados já aparecem na tabela de pesquisadores com a data da última carga atualizada, e as produções ficam disponíveis para busca imediatamente.

### Jornada 2 — Admin cadastra novo pesquisador

1. Admin clica em **"+ novo"** na toolbar da tabela de pesquisadores.
2. Admin preenche as informações básicas do pesquisador (nome, Lattes ID, departamento, campus) ou sobe um XML individual.
3. O sistema cria o registro do pesquisador e, se um XML foi fornecido, executa o pipeline de importação para esse pesquisador.
4. O novo pesquisador aparece na tabela com suas produções já carregadas e os vetores gerados.

### Jornada 3 — Admin re-sincroniza pesquisador individual

1. Admin localiza um pesquisador na tabela e clica no ícone de **re-sincronizar** (refresh) na linha correspondente.
2. Admin sobe o XML atualizado daquele pesquisador.
3. O sistema executa o pipeline completo apenas para esse XML: as produções já existentes são atualizadas via UPSERT sem duplicar, as produções novas são inseridas, e os vetores são gerados para as produções ainda não vetorizadas.
4. Admin vê a data de última carga atualizada na linha do pesquisador.

### Jornada 4 — Admin aciona geração de vetores manualmente

1. Admin percebe que a busca semântica retorna resultados vazios após uma carga.
2. A partir do painel ou diretamente pela API interna, Admin aciona a geração de vetores.
3. O sistema identifica todas as produções que ainda não têm vetor e processa cada uma.
4. Admin executa uma nova busca semântica e recebe resultados relevantes.

### Jornada 5 — Pipeline ETL aciona vetores automaticamente

1. O pipeline ETL (Apache Hop) conclui o carregamento e enriquecimento de produções.
2. Automaticamente, ao final da fase de métricas, o Hop chama o endpoint de geração de vetores com a chave de API interna.
3. O worker processa apenas as produções sem vetor — as já vetorizadas não são reprocessadas.
4. Ao final, o sistema está completamente atualizado: dados carregados, enriquecidos e com vetores prontos para busca semântica, sem nenhuma intervenção manual.

### Jornada 6 — Pipeline executado duas vezes seguidas (idempotência)

1. Admin aciona a importação de XMLs duas vezes consecutivas com os mesmos arquivos.
2. Na segunda execução, o UPSERT não cria duplicatas de pesquisadores ou produções.
3. O worker não duplica vetores já existentes — retorna 0 vetores gerados.
4. A base permanece consistente.

### Jornada 7 — Acesso não autorizado bloqueado

1. Um agente externo tenta chamar os endpoints internos sem credencial ou com credencial inválida.
2. O sistema recusa o acesso imediatamente, sem processar nenhum dado.
3. O painel admin exige autenticação antes de exibir qualquer informação ou permitir qualquer ação.

---

## 5. Core Features

### F1 — Importação de XMLs Lattes (`POST /internal/trigger-etl`)
- Recebe um ou mais arquivos XML Lattes via upload.
- Executa o pipeline completo de 6 fases em sequência (extração → transformação → Qualis → CrossRef/OpenAlex → métricas → embeddings).
- Retorna um resumo com contadores por fase: pesquisadores, produções, correspondências de enriquecimento, vetores gerados, erros.
- Suporta tanto carga em lote (múltiplos XMLs) quanto importação de um único arquivo (para cadastro ou re-sincronização de pesquisador individual).
- Requer autenticação — acesso negado sem credencial válida de Admin.

### F2 — Geração de vetores sob demanda (`POST /internal/trigger-embeddings`)
- Aciona o worker para processar todas as produções ainda sem vetor.
- Retorna o total de vetores gerados na execução.
- É idempotente: chamadas repetidas nunca duplicam vetores existentes.
- Requer autenticação — acesso negado sem credencial válida de Admin.

### F3 — Worker de geração de vetores
- Identifica automaticamente quais produções ainda não têm vetor.
- Gera o vetor de cada produção pendente a partir do título.
- Persiste cada vetor individualmente — uma falha em um item não interrompe o restante.
- Nunca sobrescreve ou duplica vetores existentes.

### F4 — Integração automática ETL → vetores
- Ao final de cada execução bem-sucedida do pipeline ETL (Apache Hop), o endpoint de geração de vetores é acionado automaticamente.
- Zero intervenção manual necessária para manter a busca semântica atualizada após uma carga via Hop.

### F5 — Gerenciamento de pesquisadores no painel admin
- O painel admin exibe a lista de pesquisadores cadastrados com nome, Lattes ID, total de produções e data da última carga.
- Admin pode filtrar e buscar pesquisadores por nome ou Lattes ID.
- Cada pesquisador na lista tem ações disponíveis: re-sincronizar (re-importar XML), editar dados cadastrais e excluir.
- O contador "sincronizados hoje" exibe quantos pesquisadores tiveram carga na data corrente.

### F6 — Documentação no Swagger
- Todos os endpoints internos aparecem na documentação interativa da API com descrição, parâmetros e exemplos de resposta.

---

## 6. Success Metrics

| Métrica | Critério de aceitação |
|---------|----------------------|
| Cobertura de vetores | 100% das produções existentes têm vetor após uma execução do worker |
| Idempotência do worker | 2 execuções consecutivas → mesmo número de vetores, sem duplicatas |
| Idempotência do ETL | 2 importações do mesmo XML → mesmos pesquisadores e produções, sem duplicatas |
| Dimensionalidade | Todos os vetores têm exatamente 384 dimensões |
| Segurança | Requisições sem credencial válida recebem 403 — confirmado em teste |
| Integração automática | Pipeline Hop aciona geração de vetores automaticamente e o worker processa as produções novas |
| Busca semântica | `POST /api/search/semantic` retorna resultados não vazios após execução do worker |
| Painel de pesquisadores | Admin visualiza lista completa com nome, Lattes ID, total de produções e data da última carga |

---

## 7. Constraints

- A geração de vetores deve usar exclusivamente modelo local — nenhuma chamada a APIs externas de embeddings.
- Os vetores devem ser compatíveis com o índice vetorial já existente no banco (384 dimensões).
- O pipeline ETL está em Apache Hop e se comunica com a API via HTTP — não via chamada Python direta.
- Acesso aos endpoints internos é restrito a requisições autenticadas como Admin.
- O worker deve ser tolerante a falhas individuais: se um embedding falhar, os demais continuam sendo processados.
- O worker não pode modificar ou deletar vetores existentes — apenas inserir para produções pendentes.
- A remoção de um pesquisador deve propagar em cascata para suas produções e vetores associados.
- Nenhuma sessão ativa de Admin pode ser acessada sem autenticação no painel.
- O worker de embeddings roda dentro do container `api` — não é um serviço Docker separado.
- O worker é um módulo Python autônomo (`backend/worker/embeddings_worker.py`) com dois caminhos de invocação: via endpoint HTTP (`POST /internal/trigger-embeddings`, usado pelo Admin e pelo Apache Hop) e via linha de comando (`python worker/embeddings_worker.py`, usado pelo Engenheiro de Dados fora da interface web). Ambos produzem o mesmo resultado no banco.
- O arquivo CSV do Qualis deve estar acessível dentro do container para que o `trigger-etl` execute o enriquecimento.

---

## 8. Assumptions

- O banco já contém produções carregadas e enriquecidas (resultado de SPK-11, SPK-12, SPK-13, SPK-89).
- A tabela `vetores` já existe no schema com o tipo correto para armazenar vetores de 384 dimensões.
- O pipeline Apache Hop (`spark_etl.hwf`) já existe com as 6 fases implementadas — a integração aqui adiciona o passo final de acionamento HTTP.
- A API FastAPI já está em execução com Docker (SPK-92, SPK-118) — os novos endpoints são acrescentados à mesma aplicação.
- O modelo de geração de vetores já está em cache local (resultado do SPK-92).
- Os 8 currículos Lattes de teste já estão carregados no banco local.
- O protótipo do frontend (`prototipo/app.html`) define a interface do painel admin — botões "importar XML", "+ novo", ações por linha (editar, re-sincronizar, excluir) e tabela de pesquisadores.
- O CSV do Qualis (`data/qualis/qualis_capes.csv`) já existe no repositório (gerado no SPK-12).

---

## 9. Out of Scope

- Implementação do frontend do painel admin (Next.js) — esta sprint entrega apenas os endpoints que o painel consumirá.
- Reprocessamento ou atualização de vetores já existentes.
- Geração de vetores a partir de campos além do título (resumo, palavras-chave).
- Agendamento automático de geração de vetores por tempo (cron).
- Monitoramento em tempo real do progresso do worker via websocket ou polling de status.
- Autenticação via Supabase Auth nos endpoints internos — usa chave de API simples via `Authorization: Bearer`.
- Criação de novas tabelas no banco — o schema já está definido.
- Edição direta de campos de produções individuais pelo Admin.
- Criação de um serviço Docker separado para o worker — ele roda dentro do container `api`.

---

## Prompt de implementação

```
Você está implementando a SPK-93 do projeto SPARK. Leia os documentos abaixo antes de qualquer ação:

1. SDD/constitution.md — princípios não negociáveis
2. SDD/plan.md — estrutura e decisões técnicas
3. SDD/memory.md — estado atual da implementação (SPK-92 e SPK-118 concluídos)
4. SDD/sprint_3/spk93_spec.md — este spec
5. prototipo/app.html — protótipo do painel admin (tela 5, seção "pesquisadores")

Contexto crítico do memory.md:
- A API FastAPI está em `backend/app/` com routers em `backend/app/routers/`
- O serviço de embeddings está em `backend/app/services/embeddings.py` (SentenceTransformer singleton)
- Docker com a API está funcional (SPK-118)
- A busca semântica retorna resultados vazios porque `vetores` está vazia — este é o problema central
- O pipeline ETL está em `etl/workflows/spark_etl.hwf` com as 6 fases já implementadas

O que implementar:

**SPK-102 — Worker de embeddings (`backend/worker/embeddings_worker.py`)**
- Query: `SELECT id, titulo FROM producoes WHERE id NOT IN (SELECT producao_id FROM vetores)`
- Para cada produção: gerar embedding via `all-MiniLM-L6-v2` (reusar o singleton de `services/embeddings.py`)
- INSERT INTO vetores (producao_id, embedding) VALUES ($1, $2)
- Executável standalone: `python backend/worker/embeddings_worker.py` (para uso direto pelo Engenheiro de Dados fora da interface web)
- Também chamado internamente pelo endpoint `POST /internal/trigger-embeddings` — ambos os caminhos produzem o mesmo resultado
- Retorna/imprime o total de vetores gerados

**SPK-103 — Endpoints internos (`backend/app/routers/internal.py`)**

`POST /internal/trigger-embeddings`
- Autenticação: `Authorization: Bearer ${INTERNAL_API_KEY}` — 403 se ausente ou inválido
- Chama o worker e retorna `{"vetores_gerados": N}`

`POST /internal/trigger-etl`
- Mesma autenticação Bearer
- Recebe arquivos XML via `multipart/form-data` (campo `files`, aceita múltiplos)
- Executa as 6 fases em sequência: extração/pesquisadores, extração/produções, Qualis, CrossRef, OpenAlex, métricas, embeddings
- Retorna JSON: `{"pesquisadores": N, "producoes": N, "qualis_match": N, "doi_fill": N, "resumo_fill": N, "jcr_fill": N, "vetores_gerados": N, "erros": [...]}`
- Suporta 1 arquivo (re-sincronização individual) ou múltiplos (importação em lote)

`GET /internal/pesquisadores`
- Retorna lista de pesquisadores com id, nome_completo, lattes_id, total_producoes, data_atualizacao
- Suporta parâmetro de busca `?q=` para filtrar por nome ou lattes_id
- Protegido por Bearer
- Serve a tabela do painel admin

`POST /internal/pesquisadores`
- Cria um novo pesquisador com os campos: nome_completo, lattes_id, departamento, campus
- UPSERT (ON CONFLICT lattes_id DO UPDATE) — nunca duplica
- Retorna o pesquisador criado/atualizado
- Protegido por Bearer

`DELETE /internal/pesquisadores/{id}`
- Remove pesquisador e, em cascata, suas produções e vetores
- Retorna 404 se não encontrado
- Protegido por Bearer

**SPK-104 — Step HTTP Client no `spark_etl.hwf`**
- Adicionar após "Pipeline Metricas" um HTTP Request para `POST /internal/trigger-embeddings`
- Header: `Authorization: Bearer ${INTERNAL_API_KEY}`
- Variável `INTERNAL_API_KEY` adicionada como parâmetro do workflow

Regras obrigatórias da constitution:
- Todo endpoint usa decorator FastAPI (Swagger funcional)
- Toda escrita em `vetores` usa INSERT — nunca UPDATE de vetores existentes
- Toda escrita em `pesquisadores` usa UPSERT (ON CONFLICT DO UPDATE)
- Autenticação com 403 para qualquer acesso não autorizado
- Remoção de pesquisador propaga em cascata para produções e vetores
- Testes unitários cobrindo: resultado com dados, resultado vazio, erro de entrada inválida

Testes obrigatórios (pytest, em `backend/tests/unit/`):
- `test_embeddings_worker.py`: produção sem vetor → vetor gerado; produção com vetor existente → não duplica; sem produções pendentes → 0 vetores; vetor gerado tem 384 dimensões
- `test_internal_endpoints.py`:
  - trigger-embeddings sem auth → 403
  - trigger-embeddings com auth válida → 200 + JSON com `vetores_gerados`
  - trigger-etl sem auth → 403
  - pesquisadores GET sem auth → 403
  - pesquisadores POST sem auth → 403

**Alterações obrigatórias no ambiente Docker:**

`backend/requirements.txt` — adicionar:
```
python-multipart>=0.0.9
```
(FastAPI exige essa lib para aceitar multipart/form-data; sem ela o trigger-etl falha em runtime)

`docker-compose.yml` — no serviço `api`, adicionar variáveis de ambiente e volume:
```yaml
volumes:
  - ./backend:/app
  - ~/.cache/huggingface:/root/.cache/huggingface
  - ./data/qualis:/app/data/qualis        # novo — CSV do Qualis acessível no container

environment:
  DATABASE_URL: ...
  INTERNAL_API_KEY: ${INTERNAL_API_KEY}              # novo
  QUALIS_CSV_PATH: /app/data/qualis/qualis_capes.csv # novo
```

`.env.example` — documentar as novas variáveis:
```
INTERNAL_API_KEY=troque-por-um-valor-secreto
QUALIS_CSV_PATH=/app/data/qualis/qualis_capes.csv
```

O worker não precisa de serviço Docker próprio — é chamado de dentro do container `api`.

Após implementar, atualize `SDD/memory.md` com o que foi feito e renomeie este spec para `spk93_spec_CONCLUIDA.md`.
```
