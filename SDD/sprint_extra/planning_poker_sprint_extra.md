# Planning Poker — Sprint Extra

**Projeto:** SPARK  
**Sprint:** Sprint Extra (pós Sprint 3)  
**Data da sessão:** 2026-06-01  
**Facilitador:** Kalvin Santos  
**Participantes:** Kalvin Santos · Glenda Santana  
**Escala:** Fibonacci (1, 2, 3, 5, 8, 13, 21)

---

## Contexto da Sprint

A Sprint Extra surgiu da necessidade de entregar funcionalidades complementares identificadas após a Sprint 3: geração de capa visual por IA para produções científicas, exibição da foto do pesquisador via proxy do Lattes/CNPq, e conclusão do spike de avaliação de modelos de embedding (SPK-14, pendente desde o backlog inicial). Todas as histórias têm escopo bem delimitado e sem dependências entre si.

**Capacidade da equipe:**  
- 2 membros × 3 dias = 6 person-days  
- Sprint curta por ser complementar à Sprint 3

---

## Rodadas de Estimativa

### SPK-119 · US-14 · Geração de capa por IA para produções científicas

> Botão "Gerar Capa com IA" na tela de detalhes de uma produção. Chama a Pollinations AI (gratuita, sem API key), gera imagem 1280×720 baseada no título e resumo, exibe como banner com overlay gradiente. Botão "Regenerar" com seed aleatório.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 3 | 3 |
| Glenda Santana | 5 | 3 |

**Discussão:**  
Glenda estimou 5 por incerteza com a API de geração de imagem (chave, formato de resposta, CORS). Kalvin explicou que a Pollinations AI é completamente aberta — sem autenticação, sem SDK, apenas um GET com o prompt na URL. O Next.js Route Handler isola a chamada server-side. O maior esforço foi o CSS (shimmer, overlay, responsividade), não a integração.

**Consenso: 3 SP**  
**Responsável:** Kalvin Santos

---

### SPK-120 · Proxy de foto do pesquisador via Lattes/CNPq

> Route Handler Next.js que busca server-side a foto do pesquisador em `servicosweb.cnpq.br`, contornando o bloqueio geográfico do CNPq (servidores Vercel nos EUA). Retorna a imagem com cache de 24h; retorna 404 se o pesquisador não tiver foto, acionando o fallback de iniciais.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 2 | 2 |
| Glenda Santana | 2 | 2 |

**Discussão:**  
Consenso imediato. A rota é simples: fetch com headers de browser brasileiro, verificação de content-type e tamanho mínimo, resposta com cache. O pattern é idêntico ao proxy do trigger-etl já implementado na Sprint 3.

**Consenso: 2 SP**  
**Responsável:** Kalvin Santos

---

### SPK-14 · Spike: Avaliação de modelos de embedding

> Comparar `all-MiniLM-L6-v2` (atual) com alternativas (MiniLM-L12, mpnet-base, multilingual-e5, OpenAI text-embedding-3) nos critérios: qualidade semântica, latência em CPU, tamanho do modelo, custo operacional e compatibilidade com o schema `VECTOR(384)`. Documentar decisão com justificativa.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 3 | 3 |
| Glenda Santana | 3 | 3 |

**Discussão:**  
Consenso imediato. É um spike de pesquisa — não envolve código, apenas análise comparativa e documentação da decisão. O esforço está concentrado em rodar queries de teste com cada modelo e documentar os scores. Não há risco de blocker.

**Consenso: 3 SP**  
**Responsável:** Glenda Santana

---

## Resumo da Estimativa

| Issue | Título resumido | Responsável | SP |
|---|---|---|---|
| SPK-119 | Geração de capa por IA | Kalvin Santos | 3 |
| SPK-120 | Proxy foto pesquisador Lattes | Kalvin Santos | 2 |
| SPK-14 | Spike modelos de embedding | Glenda Santana | 3 |
| **Total** | | | **8 SP** |

**Carga por membro:**

| Membro | Issues | SP |
|---|---|---|
| Kalvin Santos | SPK-119, SPK-120 | 5 SP |
| Glenda Santana | SPK-14 | 3 SP |

---

## Observações

- Sprint curta (3 dias úteis) — velocidade de 8 SP é compatível com a capacidade da equipe neste período.
- Todas as histórias são independentes entre si, sem dependências de bloqueio.
- SPK-14 é um spike: resultado é documento de decisão, não código entregável.
- SPK-119 e SPK-120 foram entregues no mesmo dia (01/06/2026).
