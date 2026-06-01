# Planning Poker — Sprint 3

**Projeto:** SPARK  
**Sprint:** Sprint 3  
**Data da sessão:** 12/05/2026  
**Facilitador:** Kalvin Santos  
**Participantes:** Kalvin Santos · Glenda Santana  
**Escala:** Fibonacci (1, 2, 3, 5, 8, 13, 21)

---

## Contexto da Sprint

A Sprint 3 tem como objetivo principal a construção e entrega do back-end completo da plataforma SPARK, incluindo deploy em produção no Railway. As histórias cobrem desde a configuração do banco de dados em produção até a API FastAPI com busca textual e semântica, worker de embeddings, containerização e autenticação do painel admin.

**Capacidade da equipe:**  
- 2 membros × 10 dias úteis = 20 person-days disponíveis  
- Velocidade de referência (Sprint 2): 27 SP  

---

## Rodadas de Estimativa

### SPK-91 · US-09 · Migração do schema para Supabase de produção

> Aplicar o schema completo no Supabase de produção, habilitando pgvector, RLS em todas as tabelas e validando que o ambiente está pronto para receber a API e o ETL.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 5 | 5 |
| Glenda Santana | 8 | 5 |

**Discussão:**  
Kalvin argumentou que o DDL já está definido na spec SPK-79 e a task é essencialmente executar o script no Supabase e validar o healthcheck. Glenda votou 8 por incerteza com a configuração do pgvector e RLS. Após alinhamento, concluíram que o risco é baixo pois o schema foi validado localmente.

**Consenso: 5 SP**  
**Responsável:** Kalvin Santos

---

### SPK-92 · US-10 · API FastAPI: busca textual, semântica e endpoints de suporte (local)

> Construir a API RESTful em FastAPI com todos os endpoints públicos de busca (FTS e semântica), detalhe de produção, perfil de pesquisador e stats.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 8 | 8 |
| Glenda Santana | 13 | 8 |

**Discussão:**  
Glenda estimou 13 pela quantidade de endpoints (8 rotas distintas) e pela integração com pgvector e embeddings. Kalvin lembrou que os schemas Pydantic e a estrutura de routers seguem o padrão já definido na spec SPK-92, e que o `all-MiniLM-L6-v2` já foi testado nos protótipos. A estrutura modular reduz complexidade incremental.

**Consenso: 8 SP**  
**Responsável:** Glenda Santana

---

### SPK-118 · Dockerfile da API FastAPI e integração no docker-compose

> Criar o Dockerfile da API FastAPI, integrar o serviço `api` no docker-compose existente e escrever testes de integração contra banco real.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 3 | 3 |
| Glenda Santana | 5 | 3 |

**Discussão:**  
Kalvin e Glenda divergiram apenas sobre a cobertura de testes de integração. Glenda não tinha certeza do esforço para configurar fixtures e seed de dados para o banco Docker. Kalvin argumentou que os testes reutilizam os próprios dados do ETL de teste e que o padrão pytest + httpx é direto. Convergência para 3.

**Consenso: 3 SP**  
**Responsável:** Glenda Santana

---

### SPK-93 · US-11 · Worker de embeddings e endpoints internos

> Implementar o worker de geração de embeddings, os endpoints internos trigger-etl e trigger-embeddings, e os endpoints de gerenciamento de pesquisadores do painel admin.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 13 | 8 |
| Glenda Santana | 8 | 8 |

**Discussão:**  
Kalvin votou 13 pela complexidade do pipeline ETL de 6 fases e pela integração com Apache Hop. Glenda argumentou que o worker em si é simples (SELECT + INSERT), os endpoints internos são protegidos apenas por Bearer e o Hop só precisa de um HTTP step. A maior incerteza é `python-multipart` e o volume de arquivos XML, mas é baixo risco. Kalvin aceitou 8.

**Consenso: 8 SP**  
**Responsável:** Glenda Santana

---

### SPK-94 · US-12 · Autenticação Admin e endpoints de gerenciamento de pesquisadores

> Implementar autenticação do Admin via Supabase Auth e os endpoints de gerenciamento de pesquisadores consumidos pelo painel admin.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 3 | 3 |
| Glenda Santana | 5 | 3 |

**Discussão:**  
Glenda estimou 5 por conta da configuração do RLS e da lógica de papel `admin`. Kalvin explicou que o Supabase Auth já inclui o middleware JWT pronto e que a tabela `perfis` apenas estende `auth.users` — não há implementação de auth do zero. Convergência para 3.

**Consenso: 3 SP**  
**Responsável:** Kalvin Santos

---

### SPK-95 · US-13 · Deploy do back-end no Railway

> Fazer o deploy da API FastAPI no Railway, configurar variáveis de ambiente de produção e validar que os endpoints respondem pela URL pública.

| Participante | Voto 1 | Voto final |
|---|---|---|
| Kalvin Santos | 5 | 5 |
| Glenda Santana | 5 | 5 |

**Discussão:**  
Consenso imediato. Ambos têm experiência com Railway e reconheceram que o maior esforço é configurar as variáveis de ambiente e fazer o smoke test nos endpoints. O Dockerfile já estará pronto pela SPK-118.

**Consenso: 5 SP**  
**Responsável:** Kalvin Santos

---

## Resumo da Estimativa

| Issue | Título resumido | Responsável | SP |
|---|---|---|---|
| SPK-91 | Schema Supabase produção | Kalvin Santos | 5 |
| SPK-92 | API FastAPI (busca + endpoints) | Glenda Santana | 8 |
| SPK-118 | Dockerfile + integração docker-compose | Glenda Santana | 3 |
| SPK-93 | Worker embeddings + endpoints internos | Glenda Santana | 8 |
| SPK-94 | Auth Admin + gestão de pesquisadores | Kalvin Santos | 3 |
| SPK-95 | Deploy Railway | Kalvin Santos | 5 |
| **Total** | | | **32 SP** |

**Carga por membro:**

| Membro | Issues | SP |
|---|---|---|
| Kalvin Santos | SPK-91, SPK-94, SPK-95 | 13 SP |
| Glenda Santana | SPK-92, SPK-93, SPK-118 | 19 SP |

---

## Observações

- Todas as estimativas foram realizadas com a escala Fibonacci.
- Histórias com divergência de votos tiveram discussão e nova votação antes do consenso.
- A velocidade planejada de 32 SP está próxima à velocidade histórica da equipe (27 SP na Sprint 2), aceitável dado o maior número de histórias técnicas bem definidas.
- Não há histórias acima de 8 SP — o risco de blocking é baixo.
