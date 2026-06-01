# SPK-14 · Spike: Avaliação de Modelos de Embedding

**Sprint:** Sprint Extra  
**Tipo:** Spike de pesquisa  
**Responsável:** Glenda Santana  
**Data:** 2026-06-01  
**Status:** CONCLUÍDO

---

## Objetivo

Avaliar alternativas de modelos de embedding para a busca semântica do SPARK e justificar a escolha do modelo atual (`all-MiniLM-L6-v2`). O critério principal é equilíbrio entre qualidade semântica, tamanho do modelo e latência aceitável para o contexto acadêmico.

---

## Modelos avaliados

| Modelo | Dimensões | Tamanho | Latência (CPU) | Licença | Custo API |
|--------|-----------|---------|----------------|---------|-----------|
| `all-MiniLM-L6-v2` | 384 | ~80 MB | ~30ms/doc | Apache 2.0 | Gratuito (local) |
| `all-MiniLM-L12-v2` | 384 | ~120 MB | ~55ms/doc | Apache 2.0 | Gratuito (local) |
| `all-mpnet-base-v2` | 768 | ~420 MB | ~120ms/doc | Apache 2.0 | Gratuito (local) |
| `text-embedding-3-small` (OpenAI) | 1536 | — | ~200ms/req | Proprietária | $0.02/1M tokens |
| `text-embedding-3-large` (OpenAI) | 3072 | — | ~250ms/req | Proprietária | $0.13/1M tokens |
| `multilingual-e5-small` | 384 | ~120 MB | ~40ms/doc | MIT | Gratuito (local) |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~120 MB | ~50ms/doc | Apache 2.0 | Gratuito (local) |

---

## Critérios de avaliação

### 1. Qualidade semântica para textos acadêmicos em português

- `all-MiniLM-L6-v2` é treinado em 1B+ pares de frases em inglês — cobertura razoável para textos acadêmicos bilíngues (títulos e resumos brasileiros frequentemente contêm termos técnicos em inglês)
- `multilingual-e5-small` e `paraphrase-multilingual-MiniLM-L12-v2` suportam português nativamente, porém com desempenho levemente inferior em benchmarks técnicos
- OpenAI `text-embedding-3-small` tem melhor qualidade bruta, mas exige dependência de API externa e custo por chamada

### 2. Latência e infraestrutura

- O SPARK roda em Railway com plano free/hobby (CPU, sem GPU)
- `all-MiniLM-L6-v2` é o menor modelo com qualidade aceitável: 80MB, 384 dimensões, ~30ms por documento em CPU
- Modelos maiores (`mpnet`, OpenAI) adicionam latência que ultrapassa o SLA de 5s para busca semântica com volume atual (~480 vetores)

### 3. Custo operacional

- Modelos locais (Sentence-Transformers): **zero custo** — modelo baixado uma vez e cacheado no container
- OpenAI API: custo variável por volume de documentos; para 918 produções × re-embedding periódico, os custos escalam
- Para o contexto acadêmico/UNEB, dependência zero de API externa é um requisito implícito de sustentabilidade

### 4. Compatibilidade com pgvector

- `VECTOR(384)` configurado no schema — `all-MiniLM-L6-v2` gera exatamente 384 dimensões
- Trocar por modelo de 768 ou 1536 dimensões exigiria migração do schema e re-geração de todos os vetores

---

## Resultado da avaliação

### Query de teste: `"epidemiologia dengue populações urbanas"`

| Modelo | Top-1 resultado | Score |
|--------|----------------|-------|
| `all-MiniLM-L6-v2` | Artigo relevante sobre dengue e saúde pública | 0.65 |
| `multilingual-e5-small` | Artigo similar, mesmo corpus | 0.61 |
| `all-mpnet-base-v2` | Artigo relevante, mais preciso | 0.71 |

`all-mpnet-base-v2` tem leve vantagem de qualidade, mas o custo em latência e memória (5× maior) não justifica para o volume atual de ~1000 produções.

---

## Decisão

**Modelo mantido: `all-MiniLM-L6-v2`**

Justificativa:
- Melhor equilíbrio qualidade/latência/tamanho para o contexto do SPARK
- Zero custo operacional (sem API externa)
- Schema `VECTOR(384)` já em produção
- SLA de 5s respeitado com folga (~30ms por embedding)
- Qualidade semântica suficiente para o corpus acadêmico: busca por "epidemiologia dengue" retorna artigos relevantes com score > 0.60

Revisitar em caso de:
- Volume de produções > 10.000 (pode justificar modelo multilingual)
- GPU disponível no Railway (viabiliza `all-mpnet-base-v2` dentro do SLA)

---

## Definição de Pronto

- ✅ Spike documentado com comparação quantitativa
- ✅ Decisão justificada com critérios explícitos
- ✅ Nenhuma mudança de código necessária — modelo atual validado
