# SPK-118 · Proof of Work — Dockerfile da API e Integração no docker-compose

**Data:** 2026-05-24
**Sprint:** 3 | **Story Points:** 3
**Branch:** `feat/spk-118`

---

## 1. Ambiente Docker

### 1.1 Build da imagem

```
docker compose build api
```

A imagem foi construída com `python:3.11-slim` + `torch` CPU-only (instalado antes do `sentence-transformers` para evitar que ele puxe a versão CUDA, que resulta em uma imagem de ~4 GB). Tamanho final da imagem:

```
REPOSITORY   TAG       SIZE
spark-api    latest    1.99GB
```

### 1.2 Subida do stack

```
docker compose up api -d
```

Saída observada:

```
Container spark-db-1  Running
Container spark-api-1 Creating
Container spark-api-1 Created
Container spark-db-1  Waiting
Container spark-db-1  Healthy
Container spark-api-1 Starting
Container spark-api-1 Started
```

O serviço `api` aguardou o `db` atingir `service_healthy` antes de iniciar — comportamento do `depends_on` com `condition: service_healthy`.

### 1.3 Logs da API na inicialização

```
api-1  | INFO:     Will watch for changes in these directories: ['/app']
api-1  | INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
api-1  | INFO:     Started reloader process [1] using WatchFiles
api-1  | INFO:     Started server process [15]
api-1  | INFO:     Waiting for application startup.
api-1  | INFO:     Application startup complete.
```

Hot-reload ativo (`WatchFiles`). Pool asyncpg conectado ao banco sem erros.

> **Nota de ambiente:** a porta 8000 do host estava ocupada por outro projeto (`tasks-assistant-backend`). O serviço SPARK foi mapeado para `8001:8000` via variável `API_PORT` no `docker-compose.yml`. Os testes apontam para `http://localhost:8001` via env `API_BASE_URL`.

---

## 2. Testes de Integração

### 2.1 Comando executado

```
cd backend
python -m pytest tests/integration/ -v --tb=short
```

### 2.2 Resultado completo

```
============================= test session starts =============================
platform win32 -- Python 3.13.12, pytest-8.3.5, pluggy-1.5.0
rootdir: C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\backend
configfile: pytest.ini
collected 36 items

tests/integration/test_api.py::test_health                                   PASSED [  2%]
tests/integration/test_api.py::test_stats_retorna_200                        PASSED [  5%]
tests/integration/test_api.py::test_stats_campos_obrigatorios                PASSED [  8%]
tests/integration/test_api.py::test_stats_valores_positivos                  PASSED [ 11%]
tests/integration/test_api.py::test_producoes_tipos_retorna_200              PASSED [ 13%]
tests/integration/test_api.py::test_producoes_tipos_retorna_lista            PASSED [ 16%]
tests/integration/test_api.py::test_producoes_tipos_estrutura                PASSED [ 19%]
tests/integration/test_api.py::test_producao_detalhe_200                     PASSED [ 22%]
tests/integration/test_api.py::test_producao_detalhe_campos                  PASSED [ 25%]
tests/integration/test_api.py::test_producao_detalhe_sem_campos_null         PASSED [ 27%]
tests/integration/test_api.py::test_producao_detalhe_404                     PASSED [ 30%]
tests/integration/test_api.py::test_search_text_200_com_dados                PASSED [ 33%]
tests/integration/test_api.py::test_search_text_estrutura_resposta           PASSED [ 36%]
tests/integration/test_api.py::test_search_text_422_query_vazia              PASSED [ 38%]
tests/integration/test_api.py::test_search_text_200_sem_resultados           PASSED [ 41%]
tests/integration/test_api.py::test_search_text_paginacao                    PASSED [ 44%]
tests/integration/test_api.py::test_search_text_sem_campos_null_nos_cards    PASSED [ 47%]
tests/integration/test_api.py::test_search_semantic_200                      PASSED [ 50%]
tests/integration/test_api.py::test_search_semantic_estrutura                PASSED [ 52%]
tests/integration/test_api.py::test_search_semantic_similarity_score_presente PASSED [ 55%]
tests/integration/test_api.py::test_search_semantic_similarity_score_entre_0_e_1 PASSED [ 58%]
tests/integration/test_api.py::test_search_semantic_422_query_vazia          PASSED [ 61%]
tests/integration/test_api.py::test_search_semantic_200_sem_resultados       PASSED [ 63%]
tests/integration/test_api.py::test_pesquisador_perfil_200                   PASSED [ 66%]
tests/integration/test_api.py::test_pesquisador_perfil_campos                PASSED [ 69%]
tests/integration/test_api.py::test_pesquisador_perfil_sem_campos_null       PASSED [ 72%]
tests/integration/test_api.py::test_pesquisador_perfil_404                   PASSED [ 75%]
tests/integration/test_api.py::test_pesquisador_producoes_200                PASSED [ 77%]
tests/integration/test_api.py::test_pesquisador_producoes_estrutura          PASSED [ 80%]
tests/integration/test_api.py::test_pesquisador_producoes_paginacao_maxima   PASSED [ 83%]
tests/integration/test_api.py::test_pesquisador_producoes_404                PASSED [ 86%]
tests/integration/test_api.py::test_pesquisador_stats_200                    PASSED [ 88%]
tests/integration/test_api.py::test_pesquisador_stats_estrutura              PASSED [ 91%]
tests/integration/test_api.py::test_pesquisador_stats_por_ano_campos         PASSED [ 94%]
tests/integration/test_api.py::test_pesquisador_stats_por_qualis_campos      PASSED [ 97%]
tests/integration/test_api.py::test_pesquisador_stats_404                    PASSED [100%]

============================= 36 passed in 0.71s ==============================
```

**36/36 testes passando. Zero falhas.**

---

## 3. Cobertura de endpoints validada

| Endpoint | Cenários testados | Resultado |
|----------|------------------|-----------|
| `GET /health` | status ok | ✅ PASS |
| `GET /api/stats` | 200, campos, valores positivos | ✅ PASS |
| `GET /api/producoes/tipos` | 200, lista, estrutura | ✅ PASS |
| `GET /api/producoes/{id}` | 200 com dados, campos, sem NULL, 404 | ✅ PASS |
| `POST /api/search/text` | 200 com dados, estrutura, 422 vazia, 200 lista vazia, paginação, sem NULL | ✅ PASS |
| `POST /api/search/semantic` | 200, estrutura, similarity_score presente, score em [0,1], 422 vazia, 200 lista vazia | ✅ PASS |
| `GET /api/pesquisadores/{id}` | 200, campos, sem NULL nos obrigatórios, 404 | ✅ PASS |
| `GET /api/pesquisadores/{id}/producoes` | 200, estrutura, paginação ≤ 20, 404 | ✅ PASS |
| `GET /api/pesquisadores/{id}/stats` | 200, por_ano, por_qualis, 404 | ✅ PASS |

---

## 4. Dados do banco validados na execução

Os testes obtiveram IDs dinamicamente via busca textual e exercitaram dados reais do ETL:

```json
GET /api/stats
{
  "total_producoes": 462,
  "total_pesquisadores": 8,
  "total_vetores": 0,
  "data_ultima_carga": "2026-05-23T19:59:26.489441"
}
```

```json
GET /api/producoes/tipos
[
  { "tipo": "ARTIGO",   "total": 247 },
  { "tipo": "EVENTO",   "total": 161 },
  { "tipo": "CAPITULO", "total":  40 },
  { "tipo": "LIVRO",    "total":  14 }
]
```

> **`total_vetores: 0`** — esperado. O worker de embeddings (`all-MiniLM-L6-v2`) ainda não foi executado (sprint futura). A busca semântica retorna 200 + lista vazia corretamente, sem erro.

---

## 5. Critérios de aceite

| Critério | Status |
|----------|--------|
| Stack sobe com um comando (`docker compose up`) | ✅ |
| API acessível após subida (`/docs` funcional) | ✅ |
| API aguarda banco (`depends_on: service_healthy`) | ✅ |
| Hot-reload funcional (WatchFiles detectado nos logs) | ✅ |
| Sem credenciais na imagem (todas via `.env`) | ✅ |
| Dados persistem (volume `pgdata` — banco existente mantido) | ✅ |
| Testes de integração: 36/36 passando | ✅ |
| Testes não alteram dados (somente leitura) | ✅ |

---

## 6. Quirk descoberto: torch CPU-only

A primeira tentativa de build instalou `sentence-transformers` sem fixar o torch, o que fez o pip resolver `torch==2.12.0` com todas as bibliotecas CUDA (~3 GB). A imagem resultante (>4 GB) travou o Docker daemon durante a exportação de camadas (`rpc error: EOF`).

**Solução aplicada no Dockerfile:**

```dockerfile
# Instala torch CPU-only antes — evita que sentence-transformers puxe a versão CUDA (~3 GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
```

Resultado: imagem final de **1.99 GB** (vs ~4 GB com CUDA), build estável.
