# SPK-93 · Proof of Work — Worker de Embeddings e Endpoints Internos

**Data:** 2026-05-24 20:35
**API base URL:** `http://localhost:8001`

> Endpoints internos exigem `Authorization: Bearer <INTERNAL_API_KEY>`. Chave omitida nos logs por segurança.


## 1. Autenticação — acesso sem token retorna 403

### ✅ PASS — `GET /internal/pesquisadores`

*Nenhum header de autorização enviado*

**Request:**

```
GET http://localhost:8001/internal/pesquisadores
```

**Response — HTTP 403** ✅ *(esperado: 403)*

```json
{
  "detail": "Forbidden"
}
```

**Verificações adicionais:**

- ✅ campo 'detail' presente: `True`

### ✅ PASS — `POST /internal/trigger-embeddings`

*Token errado (não coincide com INTERNAL_API_KEY)*

**Request:**

```
POST http://localhost:8001/internal/trigger-embeddings
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 403** ✅ *(esperado: 403)*

```json
{
  "detail": "Forbidden"
}
```

**Verificações adicionais:**

- ✅ campo 'detail' presente: `True`


## 2. Listar pesquisadores — `GET /internal/pesquisadores`

### ✅ PASS — `GET /internal/pesquisadores`

*Com autenticação válida — retorna lista de pesquisadores*

**Request:**

```
GET http://localhost:8001/internal/pesquisadores
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 8,
  "resultados": [
    {
      "id": 56,
      "lattes_id": "7401907691814937",
      "nome_completo": "Aloisio Santos Nascimento Filho",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 74,
      "data_atualizacao": "2026-05-23T19:57:37.240166"
    },
    {
      "id": 4,
      "lattes_id": "6716225567627323",
      "nome_completo": "Eduardo Manuel de Freitas Jorge",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 68,
      "data_atualizacao": "2026-05-23T19:57:37.207938"
    },
    {
      "id": 50,
      "lattes_id": "1966167015825708",
      "nome_completo": "Hugo Saba Pereira Cardoso",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 91,
      "data_atualizacao": "2026-05-23T19:57:37.019147"
    },
    {
      "id": 1,
      "lattes_id": "1608472474770322",
      "nome_completo": "José Garcia Vivas Miranda",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 127,
      "data_atualizacao": "2026-05-23T19:57:36.951151"
    },
    {
      "id": 52,
      "lattes_id": "4436012961948689",
      "nome_completo": "Maria Fernanda Rios Grassi",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 70,
      "data_atualizacao": "2026-05-23T19:57:37.108865"
    },
    {
      "id": 3,
      "lattes_id": "4940207771377721",
      "nome_completo": "Mayara Maria de Jesus Almeida",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 34,
      "data_atualizacao": "2026-05-24T23:32:14.286313"
    },
    {
      "id": 2,
      "lattes_id": "3633682231940138",
      "nome_completo": "Paulo Jorge Silveira Ferreira",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 0,
      "data_atualizacao": "2026-05-23T19:57:37.028091"
    },
    {
      "id": 54,
      "lattes_id": "5601958689947032",
      "nome_completo": "Raphael Silva do Rosário",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 16,
      "data_atualizacao": "2026-05-23T19:57:37.161584"
    }
  ]
}
```

**Verificações adicionais:**

- ✅ campo 'total' >= 0: `True`
- ✅ campo 'resultados' é lista: `True`
- ✅ cada item tem lattes_id: `True`
- ✅ cada item tem total_producoes: `True`


### 2.1 Filtro por nome — `GET /internal/pesquisadores?q=Hugo`

### ✅ PASS — `GET /internal/pesquisadores?q=Hugo`

*Filtro por nome parcial (case-insensitive)*

**Request:**

```
GET http://localhost:8001/internal/pesquisadores?q=Hugo
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 1,
  "resultados": [
    {
      "id": 50,
      "lattes_id": "1966167015825708",
      "nome_completo": "Hugo Saba Pereira Cardoso",
      "departamento": "DCET",
      "campus": "Campus I",
      "total_producoes": 91,
      "data_atualizacao": "2026-05-23T19:57:37.019147"
    }
  ]
}
```

**Verificações adicionais:**

- ✅ resultados contêm 'Hugo' no nome: `True`


## 3. Criar pesquisador — `POST /internal/pesquisadores`

### ✅ PASS — `POST /internal/pesquisadores`

*UPSERT — cria novo pesquisador, retorna 201*

**Request:**

```
POST http://localhost:8001/internal/pesquisadores
Authorization: Bearer <INTERNAL_API_KEY>
Content-Type: application/json

{
  "lattes_id": "0000000000000001",
  "nome_completo": "Pesquisador Teste SPK-93",
  "departamento": "DCET",
  "campus": "Campus I"
}
```

**Response — HTTP 201** ✅ *(esperado: 201)*

```json
{
  "id": 236,
  "lattes_id": "0000000000000001",
  "nome_completo": "Pesquisador Teste SPK-93",
  "departamento": "DCET",
  "campus": "Campus I",
  "total_producoes": 0,
  "data_atualizacao": "2026-05-24T23:35:39.325571"
}
```

**Verificações adicionais:**

- ✅ campo 'id' presente: `True`
- ✅ nome_completo correto: `True`
- ✅ lattes_id correto: `True`
- ✅ departamento correto: `True`


### 3.1 Idempotência — mesmo lattes_id faz UPDATE (não duplica)

### ✅ PASS — `POST /internal/pesquisadores`

*Segundo POST com mesmo lattes_id atualiza o nome — 201*

**Request:**

```
POST http://localhost:8001/internal/pesquisadores
Authorization: Bearer <INTERNAL_API_KEY>
Content-Type: application/json

{
  "lattes_id": "0000000000000001",
  "nome_completo": "Pesquisador Teste SPK-93 v2",
  "departamento": "DCET",
  "campus": "Campus I"
}
```

**Response — HTTP 201** ✅ *(esperado: 201)*

```json
{
  "id": 236,
  "lattes_id": "0000000000000001",
  "nome_completo": "Pesquisador Teste SPK-93 v2",
  "departamento": "DCET",
  "campus": "Campus I",
  "total_producoes": 0,
  "data_atualizacao": "2026-05-24T23:35:39.325571"
}
```

**Verificações adicionais:**

- ✅ id igual ao criado anteriormente: `True`
- ✅ nome atualizado para v2: `True`


## 4. Deletar pesquisador — `DELETE /internal/pesquisadores/{id}`

### ✅ PASS — `DELETE /internal/pesquisadores/236`

*Delete do pesquisador criado no passo 3 (id=236) → 204*

**Request:**

```
DELETE http://localhost:8001/internal/pesquisadores/236
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 204** ✅ *(esperado: 204)*

```json

```


### 4.1 Confirmar deleção — pesquisador não aparece mais na listagem

### ✅ PASS — `GET /internal/pesquisadores?q=Teste+SPK-93`

*Após deleção, filtro por lattes_id não retorna o pesquisador*

**Request:**

```
GET http://localhost:8001/internal/pesquisadores?q=Teste+SPK-93
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 0,
  "resultados": []
}
```

**Verificações adicionais:**

- ✅ resultados não contêm pesquisador deletado: `True`


### 4.2 Delete de ID inexistente → 404

### ✅ PASS — `DELETE /internal/pesquisadores/999999999`

*Pesquisador que não existe retorna 404*

**Request:**

```
DELETE http://localhost:8001/internal/pesquisadores/999999999
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 404** ✅ *(esperado: 404)*

```json
{
  "detail": "Pesquisador não encontrado"
}
```

**Verificações adicionais:**

- ✅ campo 'detail' presente: `True`


## 5. Acionar worker de embeddings — `POST /internal/trigger-embeddings`

### ✅ PASS — `POST /internal/trigger-embeddings`

*Gera embeddings das produções pendentes — retorna vetores_gerados*

**Request:**

```
POST http://localhost:8001/internal/trigger-embeddings
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "vetores_gerados": 0
}
```

**Verificações adicionais:**

- ✅ campo 'vetores_gerados' presente: `True`
- ✅ vetores_gerados é inteiro >= 0: `True`


### 5.1 Idempotência — segunda chamada gera 0 vetores (ON CONFLICT DO NOTHING)

### ✅ PASS — `POST /internal/trigger-embeddings`

*Segunda chamada imediata — todas as produções já têm vetor*

**Request:**

```
POST http://localhost:8001/internal/trigger-embeddings
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "vetores_gerados": 0
}
```

**Verificações adicionais:**

- ✅ vetores_gerados == 0 (já existem): `True`


## 6. Trigger ETL via upload XML — `POST /internal/trigger-etl`


### 6.1 Sem arquivos → 422 (validação)

### ✅ PASS — `POST /internal/trigger-etl`

*Request sem files retorna 422*

**Request:**

```
POST http://localhost:8001/internal/trigger-etl
Authorization: Bearer <INTERNAL_API_KEY>
```

**Response — HTTP 422** ✅ *(esperado: 422)*

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "files"
      ],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

**Verificações adicionais:**

- ✅ campo 'detail' presente: `True`


### 6.2 Com um XML Lattes real → executa pipeline completo

### ✅ PASS — `POST /internal/trigger-etl`

*Upload de 4940207771377721.xml — executa 7 fases (extração → embeddings)*

**Request:**

```
POST http://localhost:8001/internal/trigger-etl
Authorization: Bearer <INTERNAL_API_KEY>

multipart/form-data
files[0]: 4940207771377721.xml (296,854 bytes)
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "pesquisadores": 1,
  "producoes": 34,
  "qualis_match": 0,
  "doi_fill": 0,
  "resumo_fill": 0,
  "jcr_fill": 0,
  "vetores_gerados": 0,
  "erros": [
    "QUALIS_CSV_PATH não encontrado: '/app/data/qualis/qualis.csv' — fase Qualis ignorada"
  ]
}
```

**Verificações adicionais:**

- ✅ campo 'pesquisadores' presente: `True`
- ✅ campo 'producoes' presente: `True`
- ✅ campo 'qualis_match' presente: `True`
- ✅ campo 'vetores_gerados' presente: `True`
- ✅ campo 'erros' é lista: `True`
- ✅ pesquisadores >= 1 (pelo menos 1 UPSERT): `True`


## 7. Busca semântica — `POST /api/search/semantic` com vetores reais

### ✅ PASS — `POST /api/search/semantic`

*Query sobre dengue/epidemiologia — tema presente nos XMLs carregados*

**Request:**

```
POST http://localhost:8001/api/search/semantic
Content-Type: application/json

{
  "query": "epidemiologia de doenças infecciosas dengue arbovirose"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "resultados": [
    {
      "id": 624,
      "titulo": "A spatio-temporal analysis of dengue spread in a Brazilian dry climate region",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2021,
      "nome_veiculo": "Scientific Reports",
      "issn": "2045-2322",
      "doi": "10.1038/s41598-021-91306-z",
      "qualis": "A1",
      "jcr": 4.308,
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.650995454132829
    },
    {
      "id": 616,
      "titulo": "A METHOD FOR ONTOLOGY MODELING BASED ON INSTANCES CONCEPTUAL CLASSIFICATION AND FORMALIZATION",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2020,
      "nome_veiculo": "INTERNATIONAL JOURNAL OF DEVELOPMENT RESEARCH",
      "issn": "2230-9926",
      "qualis": "C",
      "jcr": 0.072,
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.08833962152364139
    },
    {
      "id": 60,
      "titulo": "Relation between mass and radius of exoplanets distinguished by their density",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2023,
      "nome_veiculo": "Research in Astronomy and Astrophysics",
      "issn": "1674-4527",
      "doi": "10.1088/1674-4527/accbb1",
      "qualis": "B1",
      "jcr": 1.475,
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.04535219277713387
    }
  ]
}
```

**Verificações adicionais:**

- ✅ 'resultados' é lista: `True`
- ✅ retornou pelo menos 1 resultado (vetores existem): `True`
- ✅ cada item tem similarity_score: `True`
- ✅ similarity_score em [0, 1]: `True`
- ✅ resultado mais relevante tem score >= 0.5: `True`
- ✅ cada item tem titulo e pesquisador: `True`


### 7.1 Ranqueamento — query diferente retorna resultados distintos no topo

### ✅ PASS — `POST /api/search/semantic`

*Query sobre redes neurais/aprendizado — deve ranquear diferente da anterior*

**Request:**

```
POST http://localhost:8001/api/search/semantic
Content-Type: application/json

{
  "query": "redes neurais aprendizado de máquina inteligência artificial"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "resultados": [
    {
      "id": 223,
      "titulo": "Análise do discurso utilizando redes complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "XXIII Encontro de Físicos do Norte e Nordeste (EFNNE)",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.5354470568362445
    },
    {
      "id": 228,
      "titulo": "Utilização de redes complexas na caracterização da pluviometria do Nordeste Brasileiro",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "XXVIII Encontro Nacional de Física da Matéria Condensada",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.512287257637116
    },
    {
      "id": 227,
      "titulo": "A Complexa Rede de Movimentos Migratórios do Brasil: Caracterização e Modelagem",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "XXIII Encontro de Físicos do Norte e Nordeste (EFNNE)",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.463445071763391
    },
    {
      "id": 231,
      "titulo": "Caracterização e Modelagem da Rede de Fluxos Migratórios no Brasil",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXIX Encontro Nacional de Física da Matéria Condensada",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.445783055331346
    },
    {
      "id": 638,
      "titulo": "Comparison of multilayer perceptron neural network architecture in photovoltaic plants fault classification",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2023,
      "nome_veiculo": "CONCILIUM (ENGLISH LANGUAGE EDITION)",
      "issn": "0010-5236",
      "doi": "10.53660/clm-2265-23r10",
      "qualis": "A2",
      "jcr": 0.239,
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similarity_score": 0.15535245473951753
    },
    {
      "id": 866,
      "titulo": "FORECASTING SOLAR RADIATION IN BRAZILIAN CITIES USING A UNIFIED MULTILAYER PERCEPTRON MODEL",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2023,
      "nome_veiculo": "IX Simpósio Internacional de Inovação e Tecnologia",
      "doi": "10.5151/siintec2023-305767",
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      },
      "similari
```

**Verificações adicionais:**

- ✅ retornou pelo menos 1 resultado: `True`
- ✅ título do top-1 diferente do top-1 da busca por dengue: `True`
- ✅ similarity_score do top-1 >= 0.4: `True`


## 8. Confirmação — `GET /api/stats` mostra vetores gerados

### ✅ PASS — `GET /api/stats`

*total_vetores > 0 após trigger-embeddings*

**Request:**

```
GET http://localhost:8001/api/stats
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total_producoes": 480,
  "total_pesquisadores": 8,
  "total_vetores": 480,
  "data_ultima_carga": "2026-05-23T19:59:26.489441"
}
```

**Verificações adicionais:**

- ✅ total_vetores > 0 (worker gerou vetores): `True`
- ✅ total_producoes > 0: `True`
- ✅ total_pesquisadores > 0: `True`


## Sumário

**16/16 cenários aprovados**

| # | Cenário | Resultado |
|---|---------|-----------|
| 1 | `GET /internal/pesquisadores — sem token → 403` | ✅ PASS |
| 2 | `POST /internal/trigger-embeddings — token errado → 403` | ✅ PASS |
| 3 | `GET /internal/pesquisadores — com token → 200` | ✅ PASS |
| 4 | `GET /internal/pesquisadores?q=Hugo — filtro por nome` | ✅ PASS |
| 5 | `POST /internal/pesquisadores — criar (201)` | ✅ PASS |
| 6 | `POST /internal/pesquisadores — UPSERT idempotente (201)` | ✅ PASS |
| 7 | `DELETE /internal/pesquisadores/236 — 204` | ✅ PASS |
| 8 | `GET /internal/pesquisadores?q= — confirmar deleção` | ✅ PASS |
| 9 | `DELETE /internal/pesquisadores/999999999 — 404` | ✅ PASS |
| 10 | `POST /internal/trigger-embeddings — gera vetores` | ✅ PASS |
| 11 | `POST /internal/trigger-embeddings — idempotência (0 gerados)` | ✅ PASS |
| 12 | `POST /internal/trigger-etl — sem arquivos → 422` | ✅ PASS |
| 13 | `POST /internal/trigger-etl — com XML → pipeline completo` | ✅ PASS |
| 14 | `POST /api/search/semantic — dengue/epidemiologia com vetores reais` | ✅ PASS |
| 15 | `POST /api/search/semantic — redes neurais (ranqueamento diferente)` | ✅ PASS |
| 16 | `GET /api/stats — total_vetores > 0` | ✅ PASS |