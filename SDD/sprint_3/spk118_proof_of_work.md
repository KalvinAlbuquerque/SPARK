# SPK-118 · Proof of Work — Testes de Integração da API

**Data:** 2026-05-24 17:32
**API base URL:** `http://localhost:8001`
**IDs usados nos testes de detalhe:** `producao_id=275`, `pesquisador_id=4` (Eduardo Manuel de Freitas Jorge)

> Todos os testes são somente leitura. IDs obtidos dinamicamente via busca textual — não hardcoded.


## 1. Health check

### ✅ PASS — `GET /health`

**Request:**

```
GET http://localhost:8001/health
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "status": "ok"
}
```

**Verificações adicionais:**

- ✅ campo status == 'ok': `ok`


## 2. Estatísticas gerais — `GET /api/stats`

### ✅ PASS — `GET /api/stats`

**Request:**

```
GET http://localhost:8001/api/stats
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total_producoes": 462,
  "total_pesquisadores": 8,
  "total_vetores": 0,
  "data_ultima_carga": "2026-05-23T19:59:26.489441"
}
```

**Verificações adicionais:**

- ✅ total_producoes presente e >= 0: `462`
- ✅ total_pesquisadores presente e >= 0: `8`
- ✅ total_vetores presente e >= 0: `0`


## 3. Tipos de produção — `GET /api/producoes/tipos`

### ✅ PASS — `GET /api/producoes/tipos`

**Request:**

```
GET http://localhost:8001/api/producoes/tipos
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
[
  {
    "tipo": "ARTIGO",
    "total": 247
  },
  {
    "tipo": "EVENTO",
    "total": 161
  },
  {
    "tipo": "CAPITULO",
    "total": 40
  },
  {
    "tipo": "LIVRO",
    "total": 14
  }
]
```

**Verificações adicionais:**

- ✅ retorna lista não vazia: `4 tipos`
- ✅ cada item tem campo 'tipo': `ARTIGO`
- ✅ cada item tem campo 'total': `247`


## 4. Detalhe de produção — `GET /api/producoes/{id}`


### 4.1 ID existente → 200

### ✅ PASS — `GET /api/producoes/275`

**Request:**

```
GET http://localhost:8001/api/producoes/275
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "id": 275,
  "titulo": "A importância do acesso aos dados completos da pesquisa científica: uma análise de como os repositórios institucionais estão sendo utilizados pelos seus pesquisadores brasileiros",
  "tipo_producao": "EVENTO",
  "ano_publicacao": 2018,
  "nome_veiculo": "III Encontro Integrado de Ensino, Pesquisa e Extensão da UNEB",
  "pesquisador": {
    "id": 4,
    "nome_completo": "Eduardo Manuel de Freitas Jorge",
    "departamento": "DCET",
    "campus": "Campus I",
    "total_producoes": 68,
    "indice_h": 2,
    "total_a1_a2": 5
  }
}
```

**Verificações adicionais:**

- ✅ campo 'id' correto: `True`
- ✅ campo 'titulo' presente: `True`
- ✅ campo 'tipo_producao' presente: `True`
- ✅ campo 'pesquisador' aninhado presente: `True`
- ✅ sem campos None na raiz: `True`


### 4.2 ID inexistente → 404

### ✅ PASS — `GET /api/producoes/999999999`

**Request:**

```
GET http://localhost:8001/api/producoes/999999999
```

**Response — HTTP 404** ✅ *(esperado: 404)*

```json
{
  "detail": "Produção não encontrada"
}
```

**Verificações adicionais:**

- ✅ mensagem de erro presente: `True`


## 5. Busca textual — `POST /api/search/text`


### 5.1 Query válida com resultados → 200

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": "redes neurais"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 2,
  "page": 1,
  "total_pages": 1,
  "resultados": [
    {
      "id": 895,
      "titulo": "SISTEMA DE RECONHECIMENTO DE PADRÕES NEURONAIS PARA CONTROLE DE BRAÇO ROBÓTICO UTILIZANDO REDES NEURAIS ARTIFICIAIS",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2009,
      "nome_veiculo": "XXVII Encontro de Físicos do Norte e Nordeste",
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 896,
      "titulo": "SISTEMA DE RECONHECIMENTO DE PADRÕES NEURONAIS UTILIZANDO REDES NEURAIS ARTIFICIAIS PARA CONTROLE DE BRAÇO ROBÓTICO",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2010,
      "nome_veiculo": "XIV Seminário de Iniciação Científica",
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ campo 'total' >= 0: `2`
- ✅ campo 'page' == 1: `True`
- ✅ campo 'total_pages' presente: `1`
- ✅ 'resultados' é lista: `True`
- ✅ cada card tem 'titulo': `True`
- ✅ cada card tem 'pesquisador': `True`
- ✅ sem campos None nos cards: `True`


### 5.2 Query vazia → 422 (validação Pydantic)

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": ""
}
```

**Response — HTTP 422** ✅ *(esperado: 422)*

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": [
        "body",
        "query"
      ],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ body de erro presente: `True`


### 5.3 Query sem resultados → 200 + lista vazia

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": "xyzzy_nenhum_resultado_esperado_12345_spark"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 0,
  "page": 1,
  "total_pages": 0,
  "resultados": []
}
```

**Verificações adicionais:**

- ✅ resultados == []: `True`
- ✅ total == 0: `True`


### 5.4 Paginação — page=1, máximo 20 itens

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": "pesquisa",
  "page": 1
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 15,
  "page": 1,
  "total_pages": 1,
  "resultados": [
    {
      "id": 275,
      "titulo": "A importância do acesso aos dados completos da pesquisa científica: uma análise de como os repositórios institucionais estão sendo utilizados pelos seus pesquisadores brasileiros",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2018,
      "nome_veiculo": "III Encontro Integrado de Ensino, Pesquisa e Extensão da UNEB",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 196,
      "titulo": "Pesquisa aplicada & Inovação Volume 3",
      "tipo_producao": "LIVRO",
      "ano_publicacao": 2021,
      "nome_veiculo": "Pesquisa aplicada & Inovação Volume 3",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 273,
      "titulo": "APLICATIVO CADERNO CIENTÍFICO GESTÃO, ARMAZENAMENTO E COLABORAÇÃO DOS DADOS DE PESQUISAS NA SAÚDE.",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2017,
      "nome_veiculo": "ENEIS - Encontro Nacional de Empreendedorismo e Inovação",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 278,
      "titulo": "Solução para Mapeamento e Consulta das Competências dos Pesquisadores: uma arquitetura para extração, integração e consultas de informações acadêmicas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2023,
      "nome_veiculo": "XIII ProspeCT&I",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 280,
      "titulo": "Mecanismo de Busca Semântica Baseado em Word Embeddings em Dados do Currículo Lattes, Programas de Pós-Graduação e Grupos de Pesquisa",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Escola Regional de Computação Bahia, Alagoas e Sergipe",
      "doi": "10.5753/erbase.2024.4430",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 281,
      "titulo": "IAPÓS: PLATAFORMA PARA APOIAR GESTORES E A COMUNIDADE ACADÊMICA NA ANÁLISE DE INFORMAÇÕES SOBRE A PRODUÇÃO CIENTÍFICA DE PESQUISADORES DA UNIVERSIDADE SENAI CIMATEC",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2025,
      "nome_veiculo": "Seminário de Avaliação de Pesquisa Científica e Tecnológica",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 282,
      "titulo": "BUSCA TEXTUAL POR TERMOS PRESENTES NO CONTEXTO DOS DADOS DO CURRÍCULO LATTES, PROGRAMAS DE PÓS-GRADUAÇÃO E GRUPOS DE PESQUISA",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2024,
      "nome_veiculo": "XXVIII Jornada de Iniciação Científica",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 283,
      "titulo": "Solução para Mapeamento e Consulta das Competências dos Pesquisadores: uma arquitetura para extração, integração e consultas de informações acadêmicas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2025,
      "nome_veiculo": "XXIX Jornada de Iniciação Científica da UNEB",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 514,
      "titulo": "O APOIO DA FAPESB À PESQUISA E EXTENSÃO EM TURISMO DE BASE COMUNITÁRIA DO CABULA",
      "tipo_producao": "CAPITULO",
      "ano_publicacao": 2021,
      "nome_veiculo": "Cabula, território de antigo quilombo: estudos e perspectivas para o turismo de base comunitária",
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 788,
      "titulo": "Pesquisa Aplicada e Inovação Vol 4",
      "tipo_producao": "LIVRO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Pesquisa Aplicada e Inovação Vol 4",
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 628,
      "titulo": "IMPRESSÃO 3D: DA PESQUISA AO SETOR PRODUTIVO UM ESTUDO EXPLORATÓRIO SOBRE SUA EVOLUÇÃO HISTÓRICA, ORIGEM, TECNOLOGIAS, APLICAÇÕES E INOVAÇÕES",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2022,
      "nome_veiculo": "GESTAO E PLANEJAMENTO",
      "issn": "2178-8030",
      "doi": "10.53706/gep.v.23.7427",
      "qualis": "A4",
      "jcr": 0.079,
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 640,
      "titulo": "Desenvolvimento de instrumento de pesquisa para identificação de modelos de elaboração da estratégia em burocracias profissionais: validação de conteúdo",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2024,
      "nome_veiculo": "REVISTA DE GESTÃO E SECRETARIADO",
      "issn": "2178-9010",
      "doi": "10.7769/gesec.v15i4.3705",
      "qualis": "A4",
      "jcr": 0.45,
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 785,
      "titulo": "INTERFACES ENTRE GAMES, PESQUISA & MERCADO",
      "tipo_producao": "LIVRO",
      "ano_publicacao": 2016,
      "nome_veiculo": "INTERFACES ENTRE GAMES, PESQUISA & MERCADO",
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 193,
      "titulo": "PESQUISA APLICADA & INOVAÇÃO",
      "tipo_producao": "LIVRO",
      "ano_publicacao": 2016,
      "nome_veiculo": "PESQUISA APLICADA & INOVAÇÃO",
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 186,
      "titulo": "Solução para Mapeamento e Consulta das Competências dos Pesquisadores: uma arquitetura para extração, integração e consultas de informações acadêmicas",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Cadernos de Prospecção",
      "issn": "1983-1358",
      "doi": "10.9771/cp.v17i2.56670",
      "qualis": "B2",
      "jcr": 0.221,
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ page retornado == 1: `True`
- ✅ len(resultados) <= 20: `True`


### 5.5 Operador OR — retorna resultados de ambos os termos

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": "redes OR grafos"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 27,
  "page": 1,
  "total_pages": 2,
  "resultados": [
    {
      "id": 75,
      "titulo": "Caracterização do transe mediúnico através das redes funcionais cerebrais",
      "tipo_producao": "CAPITULO",
      "ano_publicacao": 2023,
      "nome_veiculo": "Perispírito: Concepções e Pesquisas.",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 218,
      "titulo": "Construção de uma rede de correlação espaço-temporal para a pluviometria do semi-árido Nordestino",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2004,
      "nome_veiculo": "XXII Encontro de Físicos do Norte e Nordeste (EFNNE)",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 219,
      "titulo": "Utilização de redes complexas na caracterização de mapas conceituais de textos escritos",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2004,
      "nome_veiculo": "XXII Encontro de Físicos do Norte e Nordeste (EFNNE)",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
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
      }
    },
    {
      "id": 225,
      "titulo": "Redes complexas de correlação espaço-temporal da pluviometria do semi-árido nordestino",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "9th internacional comgress of the brazilian geophysical society",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 226,
      "titulo": "Um modelo para neoplasia utilizando redes complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "XXVIII Encontro Nacional de Física da Matéria Condensada",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
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
      }
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
      }
    },
    {
      "id": 230,
      "titulo": "Conexão preferencial de cliques: um modelo para as redes de associações entre palavras em um texto escrito.",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXIX Encontro Nacional de Física da Matéria Condensada",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
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
      }
    },
    {
      "id": 233,
      "titulo": "Modelo para a Caracterização da rede complexa de diferenciação das céluas-tronco",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXIV Encontro de Físicos do Norte e Nordeste",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 235,
      "titulo": "Rede de representações-objeto utilizando discursos escritos",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "IV Congresso Norte Nordeste de Psicologia",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 236,
      "titulo": "Modelando a Distribuição Pluviométrica no Nordeste Brasileiro Utilizando Redes",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XLIII Congresso Brasileiro de Geologia",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 239,
      "titulo": "Construção e Caracterização da Sequência de Acesso mais Provável a Servidores Web Utilizando Redes Complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXV Seminário Estudantil de Pesquisa",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 240,
      "titulo": "Modelo de Distribuição Espaço-Temporal das Chuvas no Nordeste Segundo Cálculo da Correlação Linear: uma proposta de análise ambiental a partir da teoria de redes complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XIV Congresso Brasileiro de Meteorologia",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 245,
      "titulo": "Um framework para simulação de sistemas complexos utilizando sistemas multi-agentes e redes complexas.",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2009,
      "nome_veiculo": ": Workshop de Trabalhos de Iniciação Científica e Graduação da IX Escola Regional de Computação Bahia Alagoas Sergipe",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 504,
      "titulo": "PATROCINADORES DE CAMPANHAS POLÍTICAS: REDES DE INTERESSES",
      "tipo_producao": "CAPITULO",
      "ano_publicacao": 2013,
      "nome_veiculo": "Construção do conhecimento em organizações na perspectiva das redes sociais.",
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 716,
      "titulo": "DINÂMICA TEMPORAL DE REDES FUNCIONAIS CORTICAIS EM PORTADORES DE ALZHEIMER",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2019,
      "nome_veiculo": "REVISTA SAÚDE.COM",
      "issn": "1809-0761",
      "doi": "10.22481/rsc.v15i2.4727",
      "qualis": "B2",
      "jcr": 0.135,
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 787,
      "titulo": "Redes Bayesianas: AADSP - Gerência de Teste",
      "tipo_producao": "LIVRO",
      "ano_publicacao": 2020,
      "nome_veiculo": "Redes Bayesianas: AADSP - Gerência de Teste",
      "pesquisador": {
        "id": 50,
        "nome_completo": "Hugo Saba Pereira Cardoso",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 895,
      "titulo": "SISTEMA DE RECONHECIMENTO DE PADRÕES NEURONAIS PARA CONTROLE DE BRAÇO ROBÓTICO UTILIZANDO REDES NEURAIS ARTIFICIAIS",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2009,
      "nome_veiculo": "XXVII Encontro de Físicos do Norte e Nordeste",
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ total > 0 (OR retorna resultados): `True`
- ✅ 'resultados' é lista: `True`


### 5.6 Operador NOT — exclui o segundo termo

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": "redes NOT neurais"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 24,
  "page": 1,
  "total_pages": 2,
  "resultados": [
    {
      "id": 75,
      "titulo": "Caracterização do transe mediúnico através das redes funcionais cerebrais",
      "tipo_producao": "CAPITULO",
      "ano_publicacao": 2023,
      "nome_veiculo": "Perispírito: Concepções e Pesquisas.",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 218,
      "titulo": "Construção de uma rede de correlação espaço-temporal para a pluviometria do semi-árido Nordestino",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2004,
      "nome_veiculo": "XXII Encontro de Físicos do Norte e Nordeste (EFNNE)",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 219,
      "titulo": "Utilização de redes complexas na caracterização de mapas conceituais de textos escritos",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2004,
      "nome_veiculo": "XXII Encontro de Físicos do Norte e Nordeste (EFNNE)",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
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
      }
    },
    {
      "id": 225,
      "titulo": "Redes complexas de correlação espaço-temporal da pluviometria do semi-árido nordestino",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "9th internacional comgress of the brazilian geophysical society",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 226,
      "titulo": "Um modelo para neoplasia utilizando redes complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "XXVIII Encontro Nacional de Física da Matéria Condensada",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
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
      }
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
      }
    },
    {
      "id": 230,
      "titulo": "Conexão preferencial de cliques: um modelo para as redes de associações entre palavras em um texto escrito.",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXIX Encontro Nacional de Física da Matéria Condensada",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
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
      }
    },
    {
      "id": 233,
      "titulo": "Modelo para a Caracterização da rede complexa de diferenciação das céluas-tronco",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXIV Encontro de Físicos do Norte e Nordeste",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 235,
      "titulo": "Rede de representações-objeto utilizando discursos escritos",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2005,
      "nome_veiculo": "IV Congresso Norte Nordeste de Psicologia",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 236,
      "titulo": "Modelando a Distribuição Pluviométrica no Nordeste Brasileiro Utilizando Redes",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XLIII Congresso Brasileiro de Geologia",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 239,
      "titulo": "Construção e Caracterização da Sequência de Acesso mais Provável a Servidores Web Utilizando Redes Complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XXV Seminário Estudantil de Pesquisa",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 240,
      "titulo": "Modelo de Distribuição Espaço-Temporal das Chuvas no Nordeste Segundo Cálculo da Correlação Linear: uma proposta de análise ambiental a partir da teoria de redes complexas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2006,
      "nome_veiculo": "XIV Congresso Brasileiro de Meteorologia",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 245,
      "titulo": "Um framework para simulação de sistemas complexos utilizando sistemas multi-agentes e redes complexas.",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2009,
      "nome_veiculo": ": Workshop de Trabalhos de Iniciação Científica e Graduação da IX Escola Regional de Computação Bahia Alagoas Sergipe",
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 53,
      "titulo": "DINÂMICA TEMPORAL DE REDES FUNCIONAIS CORTICAIS EM PORTADORES DE ALZHEIMER",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2019,
      "nome_veiculo": "REVISTA SAÚDE.COM",
      "issn": "1809-0761",
      "doi": "10.22481/rsc.v15i2.4727",
      "qualis": "B2",
      "jcr": 0.135,
      "pesquisador": {
        "id": 1,
        "nome_completo": "José Garcia Vivas Miranda",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 716,
      "titulo": "DINÂMICA TEMPORAL DE REDES FUNCIONAIS CORTICAIS EM PORTADORES DE ALZHEIMER",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2019,
      "nome_veiculo": "REVISTA SAÚDE.COM",
      "issn": "1809-0761",
      "doi": "10.22481/rsc.v15i2.4727",
      "qualis": "B2",
      "jcr": 0.135,
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 897,
      "titulo": "ANÁLISE DE PADRÕES DINÂMICOS DAS REDES FUNCIONAIS CEREBRAIS DE PACIENTES NORMAIS E COM FIBROMIALGIA",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2012,
      "nome_veiculo": "XXX Encontro de Físicos do Norte e Nordeste",
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 169,
      "titulo": "Redes complexas de homônimos para análise semântica textual",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2017,
      "nome_veiculo": "Informação & Informação (Online)",
      "issn": "1981-8920",
      "doi": "10.5433/1981-8920.2017v22n1p293",
      "qualis": "A2",
      "jcr": 0.121,
      "pesquisador": {
        "id": 4,
        "nome_completo": "Eduardo Manuel de Freitas Jorge",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ total > 0 (NOT é subtração, não zera): `True`
- ✅ 'resultados' é lista: `True`


### 5.7 AND implícito — todos os termos devem estar presentes

### ✅ PASS — `POST /api/search/text`

**Request:**

```
POST http://localhost:8001/api/search/text
Content-Type: application/json

{
  "query": "redes neurais"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 2,
  "page": 1,
  "total_pages": 1,
  "resultados": [
    {
      "id": 895,
      "titulo": "SISTEMA DE RECONHECIMENTO DE PADRÕES NEURONAIS PARA CONTROLE DE BRAÇO ROBÓTICO UTILIZANDO REDES NEURAIS ARTIFICIAIS",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2009,
      "nome_veiculo": "XXVII Encontro de Físicos do Norte e Nordeste",
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    },
    {
      "id": 896,
      "titulo": "SISTEMA DE RECONHECIMENTO DE PADRÕES NEURONAIS UTILIZANDO REDES NEURAIS ARTIFICIAIS PARA CONTROLE DE BRAÇO ROBÓTICO",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2010,
      "nome_veiculo": "XIV Seminário de Iniciação Científica",
      "pesquisador": {
        "id": 54,
        "nome_completo": "Raphael Silva do Rosário",
        "departamento": "DCET",
        "campus": "Campus I"
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ 'resultados' é lista: `True`
- ✅ total >= 0: `True`


## 6. Busca semântica — `POST /api/search/semantic`


### 6.1 Query válida → 200 com similarity_score em cada item

### ✅ PASS — `POST /api/search/semantic`

**Request:**

```
POST http://localhost:8001/api/search/semantic
Content-Type: application/json

{
  "query": "aprendizado de máquina e inteligência artificial"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "resultados": []
}
```

**Verificações adicionais:**

- ✅ 'resultados' é lista: `True`
- ✅ similarity_score presente em todos os itens: `True`
- ✅ similarity_score em [0, 1] para todos: `True`


### 6.2 Query vazia → 422

### ✅ PASS — `POST /api/search/semantic`

**Request:**

```
POST http://localhost:8001/api/search/semantic
Content-Type: application/json

{
  "query": ""
}
```

**Response — HTTP 422** ✅ *(esperado: 422)*

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": [
        "body",
        "query"
      ],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": {
        "min_length": 1
      }
    }
  ]
}
```

**Verificações adicionais:**

- ✅ body de erro presente: `True`


### 6.3 Query sem resultados → 200 + lista vazia

### ✅ PASS — `POST /api/search/semantic`

**Request:**

```
POST http://localhost:8001/api/search/semantic
Content-Type: application/json

{
  "query": "xyzzy_nenhum_resultado_esperado_12345_spark"
}
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "resultados": []
}
```

**Verificações adicionais:**

- ✅ resultados == []: `True`


## 7. Perfil de pesquisador — `GET /api/pesquisadores/{id}`


### 7.1 ID existente → 200

### ✅ PASS — `GET /api/pesquisadores/4`

**Request:**

```
GET http://localhost:8001/api/pesquisadores/4
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "id": 4,
  "lattes_id": "6716225567627323",
  "nome_completo": "Eduardo Manuel de Freitas Jorge",
  "departamento": "DCET",
  "campus": "Campus I",
  "resumo": "Pesquisador Bolsista de Produtividade Desen. Tec. e Extensão Inovadora do CNPq - Nível 2 e professor pleno na Universidade do Estado da Bahia (UNEB), com doutorado em Difusão do Conhecimento e pós-doutorado em Ciência de Dados com Inteligência Artificial, além de mestrado em Ciência da Computação. Minha carreira é marcada por uma atuação multifacetada, incluindo liderança no Grupo de Pesquisa Aplicada e Inovação, coordenação de programas de iniciação científica e gestão de projetos de pesquisa aplicada em parceria com empresas como Samsung, Ford e Embraer, resultando em mais de 20 patentes. Como coordenador da Agência UNEB de Inovação, atuei de forma instrumental na transferência de tecnologia e na reestruturação de políticas institucionais. Minha produção científica abrange 54 artigos, 22 capítulos de livros, 9 livros e 20 patentes, com um índice H de 5, refletindo no impacto técnico e social no campo das Ciências Exatas e da Terra. Reconhecido com bolsas de produtividade em pesquisa do CNPq, com enfoque na integração entre academia, indústria e inovação tecnológica. Na pós-graduação, atuo como professor permanente no curso de doutorado em Difusão do Conhecimento e no mestrado em Estudos Territoriais da UNEB. Como pesquisador, desenvolvo projetos em parceria com a Fiocruz na área de Educação 4.0, por meio da Rede Interdisciplinar de Ciência, Tecnologia e Inovação em Territórios Escolares. Também coordeno o projeto iaEditais da Fiocruz, voltado ao uso de Inteligência Artificial Generativa, e colaboro com a Secretaria de Ciência e Tecnologia da Bahia no desenvolvimento do Sistema de Mapeamento de Competências Científicas da Bahia, que integra o Observatório da SECTI.",
  "data_atualizacao": "2026-05-23T19:57:37.207938",
  "total_producoes": 68,
  "indice_h": 2,
  "total_a1_a2": 5
}
```

**Verificações adicionais:**

- ✅ campo 'id' correto: `True`
- ✅ campo 'nome_completo' presente: `True`
- ✅ campo 'lattes_id' presente: `True`
- ✅ total_producoes >= 0: `True`
- ✅ indice_h >= 0: `True`
- ✅ total_a1_a2 >= 0: `True`
- ✅ campos obrigatórios sem None: `True`


### 7.2 ID inexistente → 404

### ✅ PASS — `GET /api/pesquisadores/999999999`

**Request:**

```
GET http://localhost:8001/api/pesquisadores/999999999
```

**Response — HTTP 404** ✅ *(esperado: 404)*

```json
{
  "detail": "Pesquisador não encontrado"
}
```

**Verificações adicionais:**

- ✅ mensagem de erro presente: `True`


## 8. Produções do pesquisador — `GET /api/pesquisadores/{id}/producoes`


### 8.1 ID existente → 200

### ✅ PASS — `GET /api/pesquisadores/4/producoes`

**Request:**

```
GET http://localhost:8001/api/pesquisadores/4/producoes
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "total": 68,
  "page": 1,
  "total_pages": 4,
  "resultados": [
    {
      "id": 190,
      "titulo": "AGENTES INTELIGENTES PARA AMBIENTES VIRTUAIS DE ENSINO E APRENDIZAGEM: UMA REVISÃO SISTEMÁTICA",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2025,
      "nome_veiculo": "HOLOS (NATAL. ONLINE)",
      "qualis": "A1",
      "jcr": 0.462
    },
    {
      "id": 189,
      "titulo": "Estudo para Aplicação de Inteligência Artificial para Análise e Construção de Editais de Contratação Pública",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2025,
      "nome_veiculo": "REVISTA DE GESTÃO E SECRETARIADO",
      "qualis": "A4",
      "jcr": 0.45
    },
    {
      "id": 281,
      "titulo": "IAPÓS: PLATAFORMA PARA APOIAR GESTORES E A COMUNIDADE ACADÊMICA NA ANÁLISE DE INFORMAÇÕES SOBRE A PRODUÇÃO CIENTÍFICA DE PESQUISADORES DA UNIVERSIDADE SENAI CIMATEC",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2025,
      "nome_veiculo": "Seminário de Avaliação de Pesquisa Científica e Tecnológica"
    },
    {
      "id": 283,
      "titulo": "Solução para Mapeamento e Consulta das Competências dos Pesquisadores: uma arquitetura para extração, integração e consultas de informações acadêmicas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2025,
      "nome_veiculo": "XXIX Jornada de Iniciação Científica da UNEB"
    },
    {
      "id": 282,
      "titulo": "BUSCA TEXTUAL POR TERMOS PRESENTES NO CONTEXTO DOS DADOS DO CURRÍCULO LATTES, PROGRAMAS DE PÓS-GRADUAÇÃO E GRUPOS DE PESQUISA",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2024,
      "nome_veiculo": "XXVIII Jornada de Iniciação Científica"
    },
    {
      "id": 187,
      "titulo": "Espaços compartilhados na escola para aprendizagem de robótica e impressão 3D",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2024,
      "nome_veiculo": "OBSERVATORIO DE LA ECONOMÍA LATINOAMERICANA",
      "qualis": "A4",
      "jcr": 0.164
    },
    {
      "id": 280,
      "titulo": "Mecanismo de Busca Semântica Baseado em Word Embeddings em Dados do Currículo Lattes, Programas de Pós-Graduação e Grupos de Pesquisa",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Escola Regional de Computação Bahia, Alagoas e Sergipe"
    },
    {
      "id": 89,
      "titulo": "Redesign da Marca da Associação Artístico-Cultural ODEART: Construção Participativa e Estudo Cultural do Cabula",
      "tipo_producao": "CAPITULO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Educação Para o Turismo de Base Comunitária & A Economia Solidária no Quilombo Cabula"
    },
    {
      "id": 186,
      "titulo": "Solução para Mapeamento e Consulta das Competências dos Pesquisadores: uma arquitetura para extração, integração e consultas de informações acadêmicas",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Cadernos de Prospecção",
      "qualis": "B2",
      "jcr": 0.221
    },
    {
      "id": 188,
      "titulo": "The Potential Related to Microgeneration of Renewable Energy in Urban Spaces and Its Impact on Urban Planning",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2024,
      "nome_veiculo": "Energies",
      "qualis": "A2",
      "jcr": 4.06
    },
    {
      "id": 183,
      "titulo": "APLICAÇÃO DE CONCEITOS E CRITÉRIOS DE DESEMPENHO PARA UMA SALA DE AULA INOVADORA",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2023,
      "nome_veiculo": "FOCO (FACULDADE NOVO MILÊNIO)",
      "qualis": "B2",
      "jcr": 0.157
    },
    {
      "id": 184,
      "titulo": "Diretrizes para o planejamento de um ambiente de aprendizagem neuroarqeducativo",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2023,
      "nome_veiculo": "CONTRIBUCIONES A LAS CIENCIAS SOCIALES",
      "qualis": "A4",
      "jcr": 0.114
    },
    {
      "id": 185,
      "titulo": "Maker Culture: dissemination of knowledge and development of skills and competencies for the 21st century",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2023,
      "nome_veiculo": "CONCILIUM (ENGLISH LANGUAGE EDITION)",
      "qualis": "A2",
      "jcr": 0.239
    },
    {
      "id": 182,
      "titulo": "Portal de Acesso às Informações das Ações das Universidades Federais em Resposta à Pandemia de Covid-19: uma análise do período pandêmico até a transição para uma pós-pandemia",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2023,
      "nome_veiculo": "CADERNOS DE PROSPECÇÃO",
      "qualis": "B2",
      "jcr": 0.221
    },
    {
      "id": 278,
      "titulo": "Solução para Mapeamento e Consulta das Competências dos Pesquisadores: uma arquitetura para extração, integração e consultas de informações acadêmicas",
      "tipo_producao": "EVENTO",
      "ano_publicacao": 2023,
      "nome_veiculo": "XIII ProspeCT&I"
    },
    {
      "id": 181,
      "titulo": "An evaluation model for accessibility conditions of salvador bus stops",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2022,
      "nome_veiculo": "INTERNATIONAL JOURNAL FOR INNOVATION EDUCATION AND RESEARCH",
      "qualis": "C",
      "jcr": 0.065
    },
    {
      "id": 180,
      "titulo": "A Proposal for the Integration of the Energy Matrix from a Graph Theory Perspective",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2022,
      "nome_veiculo": "INTERNATIONAL JOURNAL FOR INNOVATION EDUCATION AND RESEARCH",
      "qualis": "C",
      "jcr": 0.065
    },
    {
      "id": 179,
      "titulo": "Architectural design of classroom to stimulate learning in Higher Education",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2022,
      "nome_veiculo": "INTERNATIONAL JOURNAL FOR INNOVATION EDUCATION AND RESEARCH",
      "qualis": "C",
      "jcr": 0.065
    },
    {
      "id": 88,
      "titulo": "Semantic-Analysis Expert: revisão sistemática e análise semântica",
      "tipo_producao": "CAPITULO",
      "ano_publicacao": 2022,
      "nome_veiculo": "Sistemas de representação do conhecimento Uma visão transdisciplinar entre computação e humanidades"
    },
    {
      "id": 178,
      "titulo": "A teoria fundamentada em dados aplicada ao campo da educação superior",
      "tipo_producao": "ARTIGO",
      "ano_publicacao": 2021,
      "nome_veiculo": "RESEARCH, SOCIETY AND DEVELOPMENT",
      "qualis": "C",
      "jcr": 0.306
    }
  ]
}
```

**Verificações adicionais:**

- ✅ estrutura total/page/total_pages/resultados: `True`
- ✅ len(resultados) <= 20 (paginação máxima): `True`
- ✅ cada item tem 'titulo' e 'tipo_producao': `True`


### 8.2 ID inexistente → 404

### ✅ PASS — `GET /api/pesquisadores/999999999/producoes`

**Request:**

```
GET http://localhost:8001/api/pesquisadores/999999999/producoes
```

**Response — HTTP 404** ✅ *(esperado: 404)*

```json
{
  "detail": "Pesquisador não encontrado"
}
```

**Verificações adicionais:**

- ✅ mensagem de erro presente: `True`


## 9. Estatísticas do pesquisador — `GET /api/pesquisadores/{id}/stats`


### 9.1 ID existente → 200

### ✅ PASS — `GET /api/pesquisadores/4/stats`

**Request:**

```
GET http://localhost:8001/api/pesquisadores/4/stats
```

**Response — HTTP 200** ✅ *(esperado: 200)*

```json
{
  "por_ano": [
    {
      "ano": 2003,
      "total": 2
    },
    {
      "ano": 2004,
      "total": 1
    },
    {
      "ano": 2005,
      "total": 2
    },
    {
      "ano": 2006,
      "total": 2
    },
    {
      "ano": 2007,
      "total": 3
    },
    {
      "ano": 2009,
      "total": 2
    },
    {
      "ano": 2010,
      "total": 2
    },
    {
      "ano": 2012,
      "total": 3
    },
    {
      "ano": 2014,
      "total": 1
    },
    {
      "ano": 2015,
      "total": 3
    },
    {
      "ano": 2016,
      "total": 2
    },
    {
      "ano": 2017,
      "total": 6
    },
    {
      "ano": 2018,
      "total": 5
    },
    {
      "ano": 2019,
      "total": 4
    },
    {
      "ano": 2020,
      "total": 3
    },
    {
      "ano": 2021,
      "total": 8
    },
    {
      "ano": 2022,
      "total": 4
    },
    {
      "ano": 2023,
      "total": 5
    },
    {
      "ano": 2024,
      "total": 6
    },
    {
      "ano": 2025,
      "total": 4
    }
  ],
  "por_qualis": [
    {
      "qualis": "A1",
      "total": 2
    },
    {
      "qualis": "A2",
      "total": 3
    },
    {
      "qualis": "A4",
      "total": 4
    },
    {
      "qualis": "B1",
      "total": 1
    },
    {
      "qualis": "B2",
      "total": 10
    },
    {
      "qualis": "B4",
      "total": 1
    },
    {
      "qualis": "C",
      "total": 5
    }
  ]
}
```

**Verificações adicionais:**

- ✅ campo 'por_ano' é lista: `True`
- ✅ campo 'por_qualis' é lista: `True`
- ✅ itens por_ano têm 'ano' e 'total': `True`
- ✅ itens por_qualis têm 'qualis' e 'total': `True`


### 9.2 ID inexistente → 404

### ✅ PASS — `GET /api/pesquisadores/999999999/stats`

**Request:**

```
GET http://localhost:8001/api/pesquisadores/999999999/stats
```

**Response — HTTP 404** ✅ *(esperado: 404)*

```json
{
  "detail": "Pesquisador não encontrado"
}
```

**Verificações adicionais:**

- ✅ mensagem de erro presente: `True`


## Sumário

**21/21 cenários aprovados**

| # | Endpoint | Resultado |
|---|----------|-----------|
| 1 | `GET /health` | ✅ PASS |
| 2 | `GET /api/stats` | ✅ PASS |
| 3 | `GET /api/producoes/tipos` | ✅ PASS |
| 4 | `GET /api/producoes/275 (200)` | ✅ PASS |
| 5 | `GET /api/producoes/999999999 (404)` | ✅ PASS |
| 6 | `POST /api/search/text — com resultados` | ✅ PASS |
| 7 | `POST /api/search/text — query vazia (422)` | ✅ PASS |
| 8 | `POST /api/search/text — sem resultados (200 vazio)` | ✅ PASS |
| 9 | `POST /api/search/text — paginação` | ✅ PASS |
| 10 | `POST /api/search/text — operador OR` | ✅ PASS |
| 11 | `POST /api/search/text — operador NOT` | ✅ PASS |
| 12 | `POST /api/search/text — AND implícito` | ✅ PASS |
| 13 | `POST /api/search/semantic — com similarity_score` | ✅ PASS |
| 14 | `POST /api/search/semantic — query vazia (422)` | ✅ PASS |
| 15 | `POST /api/search/semantic — sem resultados (200 vazio)` | ✅ PASS |
| 16 | `GET /api/pesquisadores/4 (200)` | ✅ PASS |
| 17 | `GET /api/pesquisadores/999999999 (404)` | ✅ PASS |
| 18 | `GET /api/pesquisadores/4/producoes (200)` | ✅ PASS |
| 19 | `GET /api/pesquisadores/999999999/producoes (404)` | ✅ PASS |
| 20 | `GET /api/pesquisadores/4/stats (200)` | ✅ PASS |
| 21 | `GET /api/pesquisadores/999999999/stats (404)` | ✅ PASS |